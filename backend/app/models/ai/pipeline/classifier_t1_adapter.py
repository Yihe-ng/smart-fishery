"""V12 T1-single 分类 adapter（移植自 model_training V12 T1Model）。

背景：V12 frozen_config 的分类器是自定义头
（YOLO11n-cls backbone + Conv + Pool + Linear(1280,128)->ReLU->Dropout->Linear(128,2)），
checkpoint 保存为自定义 `model_state` 格式，ultralytics `YOLO()` 无法直接加载，
故本 adapter 复刻训练端 T1Model 的构建/加载/前向（candidate 架构，非 final）。

输入输出契约与其它分类 adapter 一致：crops -> P(measurable) ∈ [0,1]，
class0=fish_measurable（训练端 CLASS_NAMES 合同）。
"""

from __future__ import annotations

import threading
from typing import Any, List, Optional

import numpy as np
import torch
from torch import nn

from app.models.ai.pipeline.classifier_adapters import (
    DEFAULT_CLASSIFIER_ADAPTER_REGISTRY,
    MeasurabilityClassifierProtocol,
)
from app.models.ai.pipeline.contracts import Crop


# 与训练端 expected_custom_transforms 的 Normalize 一致
_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD = (0.229, 0.224, 0.225)


class T1Model(nn.Module):
    """V12 T1Model（mode='single'）——逐项移植训练端网络结构。"""

    def __init__(self, pretrained: str):
        super().__init__()
        from ultralytics import YOLO

        yolo = YOLO(pretrained)
        seq = yolo.model
        modules = list(seq.model)
        if len(modules) < 2 or type(modules[-1]).__name__ != "Classify":
            raise RuntimeError("Unexpected YOLO11-cls model layout")
        head = modules[-1]
        self.backbone = nn.Sequential(*modules[:-1])
        self.conv = head.conv
        self.pool = head.pool
        self.d = int(head.conv.conv.out_channels)
        self.head = nn.Sequential(
            nn.Linear(self.d, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(128, 2),
        )

    def features(self, images: torch.Tensor) -> torch.Tensor:
        features = self.backbone(images)
        features = self.conv(features)
        return self.pool(features).flatten(1)

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.head(self.features(images))


def _crop_to_tensor(image_rgb: np.ndarray) -> torch.Tensor:
    """RGB uint8 (H,W,3) -> (3,H,W) float，/255 + ImageNet 归一化。"""
    float_image = image_rgb.astype(np.float32) / 255.0
    chw = np.transpose(float_image, (2, 0, 1))
    mean = np.asarray(_IMAGENET_MEAN, dtype=np.float32).reshape(3, 1, 1)
    std = np.asarray(_IMAGENET_STD, dtype=np.float32).reshape(3, 1, 1)
    normalized = (chw - mean) / std
    return torch.from_numpy(normalized)


class UltralyticsYoloClsT1Adapter(MeasurabilityClassifierProtocol):
    """V12 T1-single 分类适配器（自定义 checkpoint 格式）。"""

    backend_name = "ultralytics_yolo_cls_t1"

    def __init__(
        self,
        model_path: str,
        *,
        pretrained_path: Optional[str],
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
        if pretrained_path is None:
            raise ValueError("ultralytics_yolo_cls_t1 需要 pretrained_path")
        self._model_path = model_path
        self._pretrained_path = pretrained_path
        self._input_size = input_size
        self._positive_index = class_names.index(positive_semantic)
        self._class_names = list(class_names)
        self._threshold = threshold
        self._batch_size = batch_size
        self._temperature = temperature
        self._device = device
        self._load_lock = load_lock or threading.Lock()
        self._model: Optional[T1Model] = None

    def ensure_loaded(self) -> None:
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            try:
                checkpoint = torch.load(
                    self._model_path, map_location="cpu", weights_only=False
                )
                model = T1Model(self._pretrained_path)
                model.load_state_dict(checkpoint["model_state"])
            except Exception as exc:
                raise ValueError("CLASSIFIER_LOAD_FAILED") from exc
            model.to(torch.device(self._device))
            model.eval()
            self._model = model

    def warmup(self) -> None:
        """预留 warm-up：跑一张 dummy crop。"""
        self.ensure_loaded()
        dummy = np.zeros((self._input_size, self._input_size, 3), dtype=np.uint8)
        self.predict_proba(
            [Crop(instance_id="warmup", image_rgb=dummy, metadata={})],
            batch_size=1,
        )

    def predict_proba(
        self,
        crops: List[Crop],
        *,
        batch_size: Optional[int] = None,
    ) -> List[float]:
        if not crops:
            return []
        self.ensure_loaded()
        assert self._model is not None
        batch = batch_size or self._batch_size
        if batch <= 0:
            raise ValueError("batch_size 必须 > 0")

        probabilities: List[float] = []
        torch_device = torch.device(self._device)
        with torch.inference_mode():
            for start in range(0, len(crops), batch):
                chunk = crops[start : start + batch]
                tensors = [
                    _crop_to_tensor(crop.image_rgb) for crop in chunk
                ]
                batch_tensor = torch.stack(tensors).to(torch_device)
                try:
                    logits = self._model(batch_tensor)
                except Exception as exc:
                    raise ValueError("CLASSIFIER_INFERENCE_FAILED") from exc
                probs = torch.softmax(logits.float(), dim=1)
                positive = probs[:, self._positive_index].cpu().numpy()
                probabilities.extend(float(value) for value in positive)

        if self._temperature is not None:
            from app.models.ai.pipeline.classifier_adapters import apply_temperature

            probabilities = [
                float(apply_temperature(np.asarray([value]), self._temperature)[0])
                for value in probabilities
            ]
        if len(probabilities) != len(crops):
            raise ValueError("分类器输出数量与输入 crops 不一致")
        return probabilities

    def close(self) -> None:
        self._model = None


def _t1_factory(**kwargs) -> UltralyticsYoloClsT1Adapter:
    return UltralyticsYoloClsT1Adapter(**kwargs)


DEFAULT_CLASSIFIER_ADAPTER_REGISTRY.register(
    UltralyticsYoloClsT1Adapter.backend_name,
    _t1_factory,
)
