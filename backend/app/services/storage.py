"""统一存储抽象层：本地文件系统 / S3 兼容对象存储（MinIO 等）。

职责：对上层隐藏"文件放哪"。默认后端为 local；对象存储后端已按 S3 接口实现，
由 `STORAGE_BACKEND=object` 配合环境变量启用，未配置时不会加载，不依赖网络，
也不影响推理链路。凭据只允许来自环境变量 / backend/.env，禁止硬编码。

用法：
    storage = build_storage()
    key = storage.save_bytes("pond/r001/crop.jpg", image_bytes)
    data = storage.read_bytes(key)
"""

from __future__ import annotations

import io
import logging
from datetime import timezone
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Type

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """存储操作失败：后端未配置、对象不存在或键非法。"""


@dataclass(frozen=True)
class StorageConfig:
    """存储后端配置（immutable）。凭据为空时对象后端保持未启用。"""

    backend: str = "local"
    base_dir: str = "data/storage"
    endpoint: str = ""
    bucket: str = ""
    access_key: str = ""
    secret_key: str = ""
    secure: bool = False


class StorageBackend(ABC):
    """存储后端接口：保存 / 读取 / 删除 / 存在性。"""

    @abstractmethod
    def save_bytes(self, key: str, data: bytes) -> str:
        """保存字节内容，返回可再次访问的 key。"""

    @abstractmethod
    def read_bytes(self, key: str) -> bytes:
        """读取字节内容；对象不存在时抛 StorageError。"""

    @abstractmethod
    def delete(self, key: str) -> None:
        """删除对象，对象不存在时静默。"""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """对象是否存在。"""

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """列出指定前缀下的对象键（相对路径），供保留策略扫描使用。"""

    @abstractmethod
    def modified_time(self, key: str) -> float:
        """对象最后修改时间的 Unix 时间戳；对象不存在时抛 StorageError。"""

    @abstractmethod
    def size_of(self, key: str) -> int:
        """对象字节大小；对象不存在时抛 StorageError。"""


STORAGE_BACKENDS: Dict[str, Type[StorageBackend]] = {}


def register_storage(name: str):
    """注册存储后端，供工厂按名字解析。"""

    def decorator(cls: Type[StorageBackend]) -> Type[StorageBackend]:
        STORAGE_BACKENDS[name] = cls
        return cls

    return decorator


@register_storage("local")
class LocalStorageBackend(StorageBackend):
    """本地文件系统后端：按 base_dir 落盘，键必须是相对路径。"""

    def __init__(self, config: StorageConfig) -> None:
        self.base_dir = Path(config.base_dir)

    def _resolve(self, key: str) -> Path:
        candidate = Path(key)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise StorageError(f"非法存储键（拒绝目录穿越）: {key!r}")
        return self.base_dir / candidate

    def save_bytes(self, key: str, data: bytes) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.debug("本地存储写入: %s (%d bytes)", path, len(data))
        return key

    def read_bytes(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.is_file():
            raise StorageError(f"对象不存在: {key}")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.is_file():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()

    def list_keys(self, prefix: str = "") -> List[str]:
        root = self.base_dir
        if not root.is_dir():
            return []
        return [
            path.relative_to(root).as_posix()
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.relative_to(root).as_posix().startswith(prefix)
        ]

    def modified_time(self, key: str) -> float:
        path = self._resolve(key)
        if not path.is_file():
            raise StorageError(f"对象不存在: {key}")
        return path.stat().st_mtime

    def size_of(self, key: str) -> int:
        path = self._resolve(key)
        if not path.is_file():
            raise StorageError(f"对象不存在: {key}")
        return path.stat().st_size


@register_storage("object")
class ObjectStorageBackend(StorageBackend):
    """S3 兼容对象存储后端（MinIO / 阿里云 OSS 等）。

    依赖 `minio` 按需懒加载；endpoint 或 access_key 未配置时，任何读写调用
    都会抛 StorageError，保证未启用状态不影响进程启动。
    """

    def __init__(self, config: StorageConfig) -> None:
        self._config = config
        self._client: Optional[object] = None

    def _get_client(self) -> object:
        if self._client is not None:
            return self._client
        if not self._config.endpoint or not self._config.access_key:
            raise StorageError(
                "对象存储未配置 endpoint/access_key；请通过 STORAGE_ENDPOINT / "
                "STORAGE_ACCESS_KEY / STORAGE_SECRET_KEY 环境变量启用"
            )
        try:
            from minio import Minio
        except ImportError as exc:
            raise StorageError("未安装 minio 依赖，对象存储后端不可用") from exc
        self._client = Minio(
            self._config.endpoint,
            access_key=self._config.access_key,
            secret_key=self._config.secret_key,
            secure=self._config.secure,
        )
        return self._client

    def _ensure_bucket(self, client: object) -> None:
        if client.bucket_exists(self._config.bucket):
            return
        client.make_bucket(self._config.bucket)

    def save_bytes(self, key: str, data: bytes) -> str:
        client = self._get_client()
        self._ensure_bucket(client)
        client.put_object(self._config.bucket, key, io.BytesIO(data), len(data))
        return key

    def read_bytes(self, key: str) -> bytes:
        client = self._get_client()
        response = client.get_object(self._config.bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, key: str) -> None:
        client = self._get_client()
        try:
            client.remove_object(self._config.bucket, key)
        except Exception:
            logger.debug("对象删除已静默跳过: %s", key)

    def exists(self, key: str) -> bool:
        try:
            self._get_client().stat_object(self._config.bucket, key)
            return True
        except Exception:
            return False

    def list_keys(self, prefix: str = "") -> List[str]:
        client = self._get_client()
        return [
            obj.object_name
            for obj in client.list_objects(self._config.bucket, prefix=prefix, recursive=True)
        ]

    def modified_time(self, key: str) -> float:
        client = self._get_client()
        last = client.stat_object(self._config.bucket, key).last_modified
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return last.timestamp()

    def size_of(self, key: str) -> int:
        client = self._get_client()
        return client.stat_object(self._config.bucket, key).size


def build_storage(config: Optional[StorageConfig] = None) -> StorageBackend:
    """按配置构建存储后端；未传配置时从 Settings 读取。"""
    cfg = config or StorageConfig(
        backend=settings.STORAGE_BACKEND,
        base_dir=settings.STORAGE_LOCAL_DIR,
        endpoint=settings.STORAGE_ENDPOINT,
        bucket=settings.STORAGE_BUCKET,
        access_key=settings.STORAGE_ACCESS_KEY,
        secret_key=settings.STORAGE_SECRET_KEY,
        secure=settings.STORAGE_SECURE,
    )
    backend_cls = STORAGE_BACKENDS.get(cfg.backend)
    if backend_cls is None:
        raise StorageError(f"未知存储后端: {cfg.backend!r}（可选: {sorted(STORAGE_BACKENDS)}）")
    return backend_cls(cfg)
