"""
视频列表 API

提供视频文件列表查询接口，扫描指定目录返回可播放的视频文件列表。
"""
import os
from fastapi import APIRouter

from app.core.config import settings
from app.schemas.base import BaseResponse

router = APIRouter()

# 支持的视频格式
ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


@router.get("/list", response_model=BaseResponse[list[str]])
def get_video_list():
    """获取视频文件列表（按文件名排序）"""
    video_dir = os.path.abspath(settings.VIDEO_DIR)

    if not os.path.isdir(video_dir):
        return BaseResponse(code=200, msg="视频目录不存在", data=[])

    try:
        files = sorted([
            f"/video/{f}" for f in os.listdir(video_dir)
            if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
            and os.path.isfile(os.path.join(video_dir, f))
        ])
        return BaseResponse(code=200, msg="success", data=files)
    except OSError:
        return BaseResponse(code=200, msg="无法读取视频目录", data=[])
