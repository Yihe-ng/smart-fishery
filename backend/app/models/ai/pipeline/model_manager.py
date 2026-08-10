"""ModelManager：统一模型生命周期（懒加载/单次加载/锁/device/warm-up）。

任何 endpoint 都不得自行 new 模型；一律通过 ModelManager 获取
segmenter / classifier。未来 TensorRT adapter 在此接入。
"""

from __future__ import annotations

import threading
from typing import Optional

from app.models.ai.pipeline.classifier_adapters import (
    ClassifierAdapterRegistry,
    DEFAULT_CLASSIFIER_ADAPTER_REGISTRY,
)
from app.models.ai.pipeline import classifier_t1_adapter  # noqa: F401  # 注册 ultralytics_yolo_cls_t1
from app.models.ai.pipeline.manifest import ModelManifest
from app.models.ai.pipeline.segmenter import UltralyticsSegmenter


class ModelManager:
    """按 manifest 构建并持有分割器/分类器实例。"""

    def __init__(
        self,
        manifest: ModelManifest,
        *,
        device: str = "cpu",
        classifier_registry: Optional[ClassifierAdapterRegistry] = None,
    ):
        self._manifest = manifest
        self._device = device
        self._registry = classifier_registry or DEFAULT_CLASSIFIER_ADAPTER_REGISTRY
        # RLock：外层 ensure_loaded 与子组件 ensure_loaded 共用同一把锁，
        # 普通 Lock 会造成同线程重入死锁。
        self._load_lock = threading.RLock()
        self._segmenter: Optional[UltralyticsSegmenter] = None
        self._classifier = None
        self._loaded = False

    @property
    def manifest(self) -> ModelManifest:
        return self._manifest

    @property
    def device(self) -> str:
        return self._device

    def ensure_loaded(self) -> None:
        """懒加载（首次使用时加载，模型只加载一次）。"""
        if self._loaded:
            return
        with self._load_lock:
            if self._loaded:
                return
            seg = self._manifest.segmentation
            if seg.backend != UltralyticsSegmenter.backend_name:
                raise ValueError(f"不支持的 segmentation backend={seg.backend!r}")
            self._segmenter = UltralyticsSegmenter(
                seg.path,
                imgsz=seg.imgsz,
                conf=seg.conf,
                nms_iou=seg.nms_iou,
                retina_masks=seg.retina_masks,
                mask_policy=seg.mask_policy,
                class_names=seg.class_names,
                secondary_review_area_ratio=seg.secondary_review_area_ratio,
                device=self._device,
                load_lock=self._load_lock,
            )
            self._segmenter.ensure_loaded()

            cls = self._manifest.classifier
            self._classifier = self._registry.create(
                cls.backend,
                model_path=cls.path,
                pretrained_path=cls.pretrained_path,
                input_size=cls.input_size,
                positive_semantic=cls.positive_semantic,
                class_names=cls.class_names,
                threshold=cls.threshold,
                batch_size=cls.batch_size,
                temperature=cls.temperature,
                device=self._device,
                load_lock=self._load_lock,
            )
            self._classifier.ensure_loaded()
            self._loaded = True

    @property
    def segmenter(self) -> UltralyticsSegmenter:
        self.ensure_loaded()
        assert self._segmenter is not None
        return self._segmenter

    @property
    def classifier(self):
        self.ensure_loaded()
        assert self._classifier is not None
        return self._classifier

    def warmup(self) -> None:
        """预留 warm-up：加载后跑一次空输入，避免首请求高延迟。"""
        self.ensure_loaded()
        self._segmenter.warmup()
        self._classifier.warmup()

    def close(self) -> None:
        """释放模型（进程生命周期内通常不调用）。"""
        if self._segmenter is not None:
            self._segmenter.close()
        if self._classifier is not None:
            self._classifier.close()
        self._segmenter = None
        self._classifier = None
        self._loaded = False
