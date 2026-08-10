"""MeasurabilityClassifier 抽象 + Adapter Registry + Ultralytics YOLO-cls 适配器。

业务层只认 P(measurable) ∈ [0,1]：
- class/index 映射由 adapter 负责（positive_semantic -> class index）；
- 不暴露 YOLO result.probs / torchvision logits 结构。

Batch 合同：同帧全部 fish crops 必须优先 batch inference；支持 batch 上限、
自动 chunk、输出顺序与 instance_id 对齐（回归测试覆盖）。
"""

from __future__ import annotations

import math
import threading
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from PIL import Image

from app.models.ai.pipeline.contracts import (
    Crop,
    MeasurabilityClassifierProtocol,
)


def sigmoid(values: np.ndarray) -> np.ndarray:
    """数值稳定 sigmoid，clip 与训练端 helper 对称。"""
    clipped = np.clip(values, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def binary_logit(probability: float) -> float:
    """logit(p) = ln(p / (1 - p))，带训练端 1e-7 clip。"""
    clipped = min(max(float(probability), 1e-7), 1.0 - 1e-7)
    return math.log(clipped / (1.0 - clipped))


def apply_temperature(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    """sigmoid(logit(p) / T) —— 训练端温度校准公式。"""
    if temperature <= 0:
        raise ValueError("temperature must be a positive number")
    logits = np.asarray(
        [binary_logit(float(value)) for value in np.asarray(probabilities).ravel()]
    )
    return sigmoid(logits / float(temperature))


class UltralyticsYoloClsAdapter(MeasurabilityClassifierProtocol):
    """ultralytics_yolo_cls 适配器：加载 YOLO cls 权重并输出 P(measurable)。"""

    backend_name = "ultralytics_yolo_cls"

    def __init__(
        self,
        model_path: str,
        *,
        pretrained_path: Optional[str] = None,
        input_size: int,
        positive_semantic: str,
        class_names: List[str],
        threshold: float,
        batch_size: int = 16,
        temperature: Optional[float] = None,
        device: str = "cpu",
        load_lock: Optional[threading.Lock] = None,
    ):
        if positive_semantic not in class_names:
            raise ValueError(
                f"positive_semantic={positive_semantic!r} 不在 class_names 中"
            )
        self._model_path = model_path
        self._input_size = input_size
        self._positive_semantic = positive_semantic
        self._class_names = list(class_names)
        self._threshold = threshold
        self._batch_size = batch_size
        self._temperature = temperature
        self._device = device
        self._load_lock = load_lock or threading.Lock()
        self._model: Any = None
        self._positive_index: Optional[int] = None

    def ensure_loaded(self) -> None:
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            from ultralytics import YOLO

            self._model = YOLO(self._model_path)
            # 适配器负责 class/index 映射：按 positive_semantic 定位索引
            model_names = getattr(self._model, "names", None)
            if isinstance(model_names, dict):
                name_to_index = {str(name): int(index) for index, name in model_names.items()}
                if self._positive_semantic not in name_to_index:
                    raise ValueError(
                        f"模型类别名 {sorted(name_to_index)} 不包含 "
                        f"positive_semantic={self._positive_semantic!r}"
                    )
                self._positive_index = name_to_index[self._positive_semantic]
            elif self._positive_semantic in self._class_names:
                self._positive_index = self._class_names.index(self._positive_semantic)
            else:
                raise ValueError("无法从模型确定 positive class index")

    def warmup(self) -> None:
        """预留 warm-up：加载后跑一张 dummy crop，避免首请求延迟。"""
        self.ensure_loaded()
        dummy = np.zeros((self._input_size, self._input_size, 3), dtype=np.uint8)
        self.predict_proba(
            [
                Crop(
                    instance_id="warmup",
                    image_rgb=dummy,
                    metadata={},
                )
            ],
            batch_size=1,
        )

    def predict_proba(
        self,
        crops: List[Crop],
        *,
        batch_size: Optional[int] = None,
    ) -> List[float]:
        """输入 crops，输出与输入顺序一致的 P(measurable) 列表。"""
        if not crops:
            return []
        self.ensure_loaded()
        batch = batch_size or self._batch_size
        if batch <= 0:
            raise ValueError("batch_size 必须 > 0")

        probabilities: List[float] = []
        for start in range(0, len(crops), batch):
            chunk = crops[start : start + batch]
            pil_images = [Image.fromarray(crop.image_rgb) for crop in chunk]
            try:
                results = self._model.predict(
                    pil_images,
                    imgsz=self._input_size,
                    verbose=False,
                    device=self._device,
                )
            except Exception as exc:
                raise ValueError("CLASSIFIER_INFERENCE_FAILED") from exc

            for result in results:
                probs = result.probs
                if probs is None:
                    raise ValueError("分类模型未返回 probs")
                data = probs.data  # (C,) float tensor
                if hasattr(data, "cpu"):
                    data = data.cpu().numpy()
                data = np.asarray(data, dtype=np.float64)
                if self._positive_index is None or self._positive_index >= len(data):
                    raise ValueError("分类模型输出与 positive class index 不匹配")
                probability = float(data[self._positive_index])
                if self._temperature is not None:
                    probability = float(apply_temperature(
                        np.asarray([probability]), self._temperature
                    )[0])
                probabilities.append(probability)

        if len(probabilities) != len(crops):
            raise ValueError("分类器输出数量与输入 crops 不一致")
        return probabilities

    def close(self) -> None:
        self._model = None
        self._positive_index = None


# ---------------------------------------------------------------------------
# Adapter Registry：新增 backbone 只需注册工厂，业务层零改动
# ---------------------------------------------------------------------------


ClassifierAdapterFactory = Callable[..., MeasurabilityClassifierProtocol]


class ClassifierAdapterRegistry:
    """分类 adapter 注册表。

    当前真实支持：ultralytics_yolo_cls。
    接口允许以后增加：torchvision_resnet / torchvision_efficientnet /
    torchvision_mobilenet / learned_temporal_head 等。
    """

    def __init__(self) -> None:
        self._factories: Dict[str, ClassifierAdapterFactory] = {}

    def register(self, backend_name: str, factory: ClassifierAdapterFactory) -> None:
        if not backend_name or not callable(factory):
            raise ValueError("backend_name 必须非空且 factory 必须可调用")
        self._factories[backend_name] = factory

    def create(self, backend_name: str, **kwargs) -> MeasurabilityClassifierProtocol:
        if backend_name not in self._factories:
            raise ValueError(
                f"未注册的分类 backend={backend_name!r}，"
                f"已注册: {sorted(self._factories)}"
            )
        return self._factories[backend_name](**kwargs)

    def registered(self) -> List[str]:
        return sorted(self._factories)


def _ultralytics_cls_factory(**kwargs) -> UltralyticsYoloClsAdapter:
    return UltralyticsYoloClsAdapter(**kwargs)


DEFAULT_CLASSIFIER_ADAPTER_REGISTRY = ClassifierAdapterRegistry()
DEFAULT_CLASSIFIER_ADAPTER_REGISTRY.register(
    UltralyticsYoloClsAdapter.backend_name,
    _ultralytics_cls_factory,
)
