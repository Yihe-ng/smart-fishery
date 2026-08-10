"""FishAnalysisPipeline 部署基础架构包。

目标：让 Growth API 与具体模型实现（YOLO/ResNet/MobileNet/TensorRT）解耦，
通过 FishSegmenter / CropBuilder / MeasurabilityClassifier / TemporalProcessor /
FishLengthMeasurement 五个组件 + Adapter Registry + Model Manifest 实现
“换权重/换 adapter/换 manifest，而不重写 endpoint”。

本包所有模型产物均为 candidate（候选），禁止标记 final。
"""

from app.models.ai.pipeline.contracts import (
    Crop,
    FishInstance,
    FishSegmenterProtocol,
    FrameAnalysisOutput,
    MeasurabilityClassifierProtocol,
    PipelineFish,
    TemporalOutcome,
    TemporalPolicyProtocol,
)
from app.models.ai.pipeline.crop_builder import CropBuilder
from app.models.ai.pipeline.manifest import ModelManifest, load_manifest
from app.models.ai.pipeline.pipeline import FishAnalysisPipeline

__all__ = [
    "Crop",
    "CropBuilder",
    "FishAnalysisPipeline",
    "FishInstance",
    "FishSegmenterProtocol",
    "FrameAnalysisOutput",
    "MeasurabilityClassifierProtocol",
    "ModelManifest",
    "PipelineFish",
    "TemporalOutcome",
    "TemporalPolicyProtocol",
    "load_manifest",
]
