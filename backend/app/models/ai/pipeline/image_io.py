"""图像输入解码（base64 -> RGB uint8 numpy）。

错误码与 legacy 路径保持一致：
IMAGE_DECODE_FAILED / INVALID_IMAGE / IMAGE_TOO_LARGE。
"""

from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 12_000_000

MIME_BY_FORMAT = {
    "JPEG": "image/jpeg",
    "JPG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "BMP": "image/bmp",
}


def decode_base64_to_rgb(image_base64: str) -> tuple[np.ndarray, dict]:
    """解码 base64 图像为 RGB uint8 numpy 数组。

    Returns
    -------
    (image_rgb, meta)
      image_rgb : (H, W, 3) uint8 RGB
      meta : {src, width, height, format}
    """
    try:
        image_data = base64.b64decode(image_base64, validate=True)
    except Exception as exc:
        raise ValueError("IMAGE_DECODE_FAILED") from exc

    if not image_data:
        raise ValueError("INVALID_IMAGE")
    if len(image_data) > MAX_IMAGE_BYTES:
        raise ValueError("IMAGE_TOO_LARGE")

    try:
        pil_image = Image.open(io.BytesIO(image_data))
        pil_image.load()
    except UnidentifiedImageError as exc:
        raise ValueError("INVALID_IMAGE") from exc
    except Exception as exc:
        raise ValueError("IMAGE_DECODE_FAILED") from exc

    if pil_image.width <= 0 or pil_image.height <= 0:
        raise ValueError("INVALID_IMAGE")
    if pil_image.width * pil_image.height > MAX_IMAGE_PIXELS:
        raise ValueError("IMAGE_TOO_LARGE")

    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    image_rgb = np.asarray(pil_image, dtype=np.uint8)

    meta = {
        "src": _build_data_url(image_base64, pil_image.format),
        "width": pil_image.width,
        "height": pil_image.height,
        "format": pil_image.format,
    }
    return image_rgb, meta


def _build_data_url(image_base64: str, image_format: str | None) -> str:
    mime_type = MIME_BY_FORMAT.get((image_format or "").upper(), "image/png")
    return f"data:{mime_type};base64,{image_base64}"
