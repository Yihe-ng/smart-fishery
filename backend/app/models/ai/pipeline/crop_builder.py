"""CropBuilder：复刻训练端 crop 合同。

合同（model_training v8/v10/v12 frozen config）：
    predicted mask tight bbox
    -> 1.30x 扩展（margin=0.15 每侧）
    -> 正方形
    -> 越界先平移（translate window in bounds）
    -> 必要时 padding 127
    -> RGB
    -> resize 224x224

本实现与训练端 `create_fish_measurability_crop_preview.square_crop` 数学一致
（golden 测试覆盖）。输入输出均为 RGB uint8 numpy，不做 BGR/RGB 翻转；
通道转换由具体模型 adapter 负责。
"""

from __future__ import annotations

import math
from typing import Optional

import cv2
import numpy as np

from app.models.ai.pipeline.contracts import Crop, FishInstance


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int]:
    """bool mask 的 tight bbox，exclusive (x0, y0, x1, y1)，与训练端一致。"""
    ys, xs = np.where(mask)
    if not len(xs):
        raise ValueError("Cannot crop an empty mask")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def mask_touches_border(mask: np.ndarray, margin: int = 1) -> bool:
    """mask 是否触及图像最外层 margin 行列（用于元数据/可测性诊断）。"""
    if mask.ndim != 2 or mask.shape[0] <= margin * 2 or mask.shape[1] <= margin * 2:
        return True
    if mask[:margin, :].any() or mask[-margin:, :].any():
        return True
    if mask[:, :margin].any() or mask[:, -margin:].any():
        return True
    return False


def square_crop(
    image_rgb: np.ndarray,
    mask: np.ndarray,
    *,
    margin: float,
    tile_size: Optional[int],
    padding_value: int = 127,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """复刻训练端 square_crop：扩展->正方形->先平移->后 padding->resize。

    Returns
    -------
    (crop_rgb, crop_mask, contract)
      crop_rgb : uint8 (side, side, 3) 或 (tile_size, tile_size, 3)，RGB
      crop_mask : bool (同尺寸)
      contract : crop 元数据（窗口、平移量、padding、mask area 等）
    """
    height, width = image_rgb.shape[:2]
    if mask.shape != (height, width):
        raise ValueError(
            f"mask 形状 {mask.shape} 与图像形状 {(height, width)} 不一致"
        )
    mask_bool = mask.astype(bool)

    x0, y0, x1, y1 = bbox_from_mask(mask_bool)
    object_width = x1 - x0
    object_height = y1 - y0
    expanded_width = max(1, int(math.ceil(object_width * (1 + 2 * margin))))
    expanded_height = max(1, int(math.ceil(object_height * (1 + 2 * margin))))
    side = max(expanded_width, expanded_height)
    center_x = (x0 + x1) / 2
    center_y = (y0 + y1) / 2
    left = int(math.floor(center_x - side / 2))
    top = int(math.floor(center_y - side / 2))
    right = left + side
    bottom = top + side
    centered_window = [left, top, right, bottom]

    # 合同：越界先平移（尽量保留真实像素），padding 只是兜底
    if side <= width:
        left = min(max(left, 0), width - side)
        right = left + side
    if side <= height:
        top = min(max(top, 0), height - side)
        bottom = top + side

    src_left = max(0, left)
    src_top = max(0, top)
    src_right = min(width, right)
    src_bottom = min(height, bottom)
    dst_left = src_left - left
    dst_top = src_top - top
    dst_right = dst_left + (src_right - src_left)
    dst_bottom = dst_top + (src_bottom - src_top)

    crop = np.full((side, side, 3), padding_value, dtype=np.uint8)
    crop_mask = np.zeros((side, side), dtype=np.uint8)
    crop[dst_top:dst_bottom, dst_left:dst_right] = image_rgb[
        src_top:src_bottom, src_left:src_right
    ]
    crop_mask[dst_top:dst_bottom, dst_left:dst_right] = mask_bool[
        src_top:src_bottom, src_left:src_right
    ].astype(np.uint8)

    if tile_size is None:
        output = crop
        output_mask = crop_mask.astype(bool)
    else:
        interpolation = cv2.INTER_AREA if side > tile_size else cv2.INTER_LINEAR
        output = cv2.resize(crop, (tile_size, tile_size), interpolation=interpolation)
        output_mask = cv2.resize(
            crop_mask, (tile_size, tile_size), interpolation=cv2.INTER_NEAREST
        ).astype(bool)

    contract = {
        "object_bbox_xyxy_exclusive": [x0, y0, x1, y1],
        "centered_crop_window_xyxy_exclusive": centered_window,
        "crop_window_xyxy_exclusive": [left, top, right, bottom],
        "window_shift_xy": [left - centered_window[0], top - centered_window[1]],
        "padding_ltrb": [
            max(0, -left),
            max(0, -top),
            max(0, right - width),
            max(0, bottom - height),
        ],
        "source_side_px": side,
        "output_side_px": int(output.shape[0]),
        "mask_area_px": int(mask_bool.sum()),
        "touches_image_border": mask_touches_border(mask_bool),
    }
    return output, output_mask, contract


def mask_focus(image_rgb: np.ndarray, mask: np.ndarray, outside_brightness: float) -> np.ndarray:
    """训练端 Mask Focus：mask 外像素调暗到 outside_brightness，mask 内保留。"""
    dimmed = np.round(image_rgb.astype(np.float32) * outside_brightness).astype(np.uint8)
    output = dimmed
    output[mask] = image_rgb[mask]
    return output


class CropBuilder:
    """按 manifest crop 配置为每条鱼构建分类输入 crop。"""

    def __init__(
        self,
        *,
        margin_fraction_each_side: float,
        bbox_scale: float,
        tile_size: int,
        padding_value: int,
        mask_focus_outside_brightness: Optional[float] = None,
    ):
        if margin_fraction_each_side < 0:
            raise ValueError("margin_fraction_each_side 必须 >= 0")
        if bbox_scale <= 0:
            raise ValueError("bbox_scale 必须 > 0")
        self._margin = margin_fraction_each_side
        self._tile_size = tile_size
        self._padding_value = padding_value
        self._mask_focus_brightness = mask_focus_outside_brightness
        # 合同：bbox_scale 与 margin 的等价关系校验（1.30x == margin 0.15）
        expected_margin = (bbox_scale - 1.0) / 2.0
        if abs(expected_margin - margin_fraction_each_side) > 1e-6:
            raise ValueError(
                f"crop 配置不一致：bbox_scale={bbox_scale} 对应 margin="
                f"{expected_margin}，但配置了 margin={margin_fraction_each_side}"
            )

    def build(self, image_rgb: np.ndarray, instance: FishInstance) -> Crop:
        """为单条鱼构建 crop。输入为 RGB uint8 (H,W,3)。"""
        crop_rgb, crop_mask, metadata = square_crop(
            image_rgb,
            instance.mask,
            margin=self._margin,
            tile_size=self._tile_size,
            padding_value=self._padding_value,
        )
        if self._mask_focus_brightness is not None:
            crop_rgb = mask_focus(crop_rgb, crop_mask, self._mask_focus_brightness)
        metadata["instance_id"] = instance.instance_id
        metadata["segmentation_confidence"] = float(instance.segmentation_confidence)
        return Crop(
            instance_id=instance.instance_id,
            image_rgb=crop_rgb,
            metadata=metadata,
        )

    def build_many(
        self, image_rgb: np.ndarray, instances: list[FishInstance]
    ) -> list[Crop]:
        """批量构建，保持与 instances 顺序一致（instance_id 对齐）。"""
        return [self.build(image_rgb, instance) for instance in instances]
