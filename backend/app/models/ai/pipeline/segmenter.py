"""FishSegmenter 抽象与 Ultralytics 适配器。

业务层不直接依赖 Ultralytics Results：adapter 把 Results 转换为
标准 FishInstance（instance_id / bbox_xyxy / mask / seg_confidence /
source_shape）。mask 后处理（最大 8 连通块）与训练端冻结配置一致。
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from app.models.ai.pipeline.contracts import FishInstance, FishSegmenterProtocol


def clean_disconnected_components(
    mask: np.ndarray,
    secondary_review_area_ratio: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    """复刻训练端 mask 清理：只保留最大 8 连通块。

    Returns
    -------
    (cleaned_bool, audit)
    """
    component_count, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8),
        connectivity=8,
    )
    areas = [
        (label, int(stats[label, cv2.CC_STAT_AREA]))
        for label in range(1, component_count)
    ]
    areas.sort(key=lambda item: item[1], reverse=True)
    if not areas:
        raise ValueError("Cannot clean an empty prediction mask")
    largest_area = areas[0][1]
    kept_labels = {areas[0][0]}
    cleaned = np.isin(labels, list(kept_labels))
    removed = [(label, area) for label, area in areas if label not in kept_labels]
    secondary_ratio = areas[1][1] / largest_area if len(areas) > 1 else 0.0
    audit = {
        "connectivity": 8,
        "classification_mask_policy": "largest_connected_component_only",
        "secondary_review_area_ratio": secondary_review_area_ratio,
        "raw_component_count": len(areas),
        "raw_component_areas_px": [area for _, area in areas],
        "largest_component_area_px": largest_area,
        "secondary_component_area_ratio": round(float(secondary_ratio), 6),
        "kept_component_count": len(kept_labels),
        "removed_component_count": len(removed),
        "removed_component_areas_px": [area for _, area in removed],
        "removed_area_px": sum(area for _, area in removed),
        "mask_island_removed": bool(removed),
        "multi_component_review": secondary_ratio >= secondary_review_area_ratio,
    }
    return cleaned, audit


def _mask_to_bool(mask_data: Any, height: int, width: int) -> np.ndarray:
    """YOLO mask tensor -> 全分辨率 bool 数组（尺寸不符 INTER_NEAREST resize）。"""
    if hasattr(mask_data, "detach"):
        mask = mask_data.detach().cpu().numpy()
    else:
        mask = np.asarray(mask_data)
    mask = np.squeeze(mask)
    if mask.ndim != 2:
        raise ValueError("mask 必须是二维数组")
    if mask.shape != (height, width):
        mask = cv2.resize(
            mask.astype(np.float32),
            (width, height),
            interpolation=cv2.INTER_NEAREST,
        )
    return (mask > 0.5).astype(bool)


def _mask_tight_bbox(mask: np.ndarray) -> tuple[float, float, float, float]:
    ys, xs = np.where(mask)
    if not len(xs):
        raise ValueError("empty mask")
    return (
        float(xs.min()),
        float(ys.min()),
        float(xs.max()) + 1.0,
        float(ys.max()) + 1.0,
    )


class UltralyticsSegmenter(FishSegmenterProtocol):
    """Ultralytics YOLO seg 适配器（当前唯一真实 backend，未来可换 TensorRT）。"""

    backend_name = "ultralytics_seg"

    def __init__(
        self,
        model_path: str,
        *,
        imgsz: int,
        conf: float,
        nms_iou: float,
        retina_masks: bool = True,
        mask_policy: str = "largest_connected_component",
        class_names: Optional[List[str]] = None,
        secondary_review_area_ratio: float = 0.05,
        device: str = "cpu",
        load_lock: Optional[threading.Lock] = None,
    ):
        self._model_path = model_path
        self._imgsz = imgsz
        self._conf = conf
        self._nms_iou = nms_iou
        self._retina_masks = retina_masks
        self._mask_policy = mask_policy
        self._class_names = class_names or []
        self._secondary_review_area_ratio = secondary_review_area_ratio
        self._device = device
        self._load_lock = load_lock or threading.Lock()
        self._model: Any = None

    # -- 模型生命周期（由 ModelManager 统一管理） ---------------------------
    def ensure_loaded(self) -> None:
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            from ultralytics import YOLO

            self._model = YOLO(self._model_path)

    def warmup(self) -> None:
        """预留 warm-up 接口：加载后用 1 帧空图跑一次，避免首请求延迟。"""
        self.ensure_loaded()
        dummy = np.zeros((self._imgsz, self._imgsz, 3), dtype=np.uint8)
        self.predict(dummy)

    # -- 统一接口 -----------------------------------------------------------
    def predict(self, image_rgb: np.ndarray) -> List[FishInstance]:
        if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
            raise ValueError("segmenter 输入必须是 (H, W, 3) RGB 图像")
        height, width = image_rgb.shape[:2]
        self.ensure_loaded()
        try:
            # 管线统一接收 RGB；Ultralytics 的 numpy 输入按 BGR 解释，推理前必须转换通道。
            model_input = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            results = self._model.predict(
                model_input,
                imgsz=self._imgsz,
                conf=self._conf,
                iou=self._nms_iou,
                retina_masks=self._retina_masks,
                verbose=False,
                device=self._device,
            )
        except Exception as exc:
            raise ValueError("MODEL_INFERENCE_FAILED") from exc

        instances: List[FishInstance] = []
        instance_counter = 0
        for result in results:
            boxes = result.boxes
            masks = result.masks
            if boxes is None or len(boxes) == 0:
                continue
            for i, box in enumerate(boxes):
                if masks is None or i >= len(masks):
                    continue
                class_name = result.names[int(box.cls[0])] if result.names else None
                raw_mask = masks.data[i]
                try:
                    mask_bool = _mask_to_bool(raw_mask, height, width)
                except Exception:
                    continue
                component_audit: dict[str, Any] = {}
                if self._mask_policy == "largest_connected_component":
                    mask_bool, component_audit = clean_disconnected_components(
                        mask_bool, self._secondary_review_area_ratio
                    )
                elif self._mask_policy == "raw":
                    pass
                else:
                    raise ValueError(f"不支持的 mask_policy={self._mask_policy}")
                if not mask_bool.any():
                    continue
                bbox_xyxy = _mask_tight_bbox(mask_bool)
                instances.append(
                    FishInstance(
                        instance_id=f"inst-{instance_counter}",
                        bbox_xyxy=bbox_xyxy,
                        mask=mask_bool,
                        segmentation_confidence=float(box.conf[0]),
                        source_shape=(width, height),
                        class_name=class_name,
                        metadata={"cleaned_component_audit": component_audit},
                    )
                )
                instance_counter += 1
        return instances

    def close(self) -> None:
        """释放模型引用（模型只加载一次，由 ModelManager 生命周期管理）。"""
        self._model = None
