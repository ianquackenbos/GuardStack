"""
Storage Service

S3-compatible object storage for models and artifacts.
"""

import asyncio
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncGenerator, BinaryIO, Optional

import aioboto3
from botocore.config import Config

from guardstack.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Storage configuration."""
    
    default_bucket: str = "guardstack"
    region: str = "us-east-1"
    max_pool_connections: int = 10


class StorageService:
    """
    S3-compatible storage service.
    
    Provides:
    - Object upload/download
    - Presigned URLs
    - Bucket management
    - Streaming support
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        config: Optional[StorageConfig] = None,
    ) -> None:
        self.settings = settings or Settings()
        self.config = config or StorageConfig()
        self._session: Optional[aioboto3.Session] = None
    
    @property
    def session(self) -> aioboto3.Session:
        """Get or create the aioboto3 session."""
        if self._session is None:
            self._session = aioboto3.Session()
        return self._session
    
    def _get_client_config(self) -> dict[str, Any]:
        """Get S3 client configuration."""
        return {
            "endpoint_url": self.settings.s3_endpoint,
            "aws_access_key_id": self.settings.s3_access_key,
            "aws_secret_access_key": self.settings.s3_secret_key,
            "region_name": self.config.region,
            "config": Config(
                max_pool_connections=self.config.max_pool_connections,
                signature_version="s3v4",
            ),
        }
    
    # ==================== Bucket Operations ====================
    
    async def create_bucket(self, bucket: str) -> bool:
        """Create a bucket if it doesn't exist."""
        async with self.session.client("s3", **self._get_client_config()) as s3:
            try:
                await s3.head_bucket(Bucket=bucket)
                return True  # Bucket exists
            except Exception:
                pass
            
            try:
                await s3.create_bucket(Bucket=bucket)
                logger.info(f"Created bucket: {bucket}")
                return True
            except Exception as e:
                logger.error(f"Failed to create bucket {bucket}: {e}")
                return False
    
    async def list_buckets(self) -> list[str]:
        """List all buckets."""
        async with self.session.client("s3", **self._get_client_config()) as s3:
            response = await s3.list_buckets()
            return [b["Name"] for b in response.get("Buckets", [])]
    
    async def delete_bucket(self, bucket: str, force: bool = False) -> bool:
        """
        Delete a bucket.
        
        Args:
            bucket: Bucket name
            force: Delete all objects first
        
        Returns:
            True if successful
        """
        async with self.session.client("s3", **self._get_client_config()) as s3:
            if force:
                # Delete all objects first
                async for obj in self.list_objects(bucket):
                    await self.delete(bucket, obj["key"])
            
            try:
                await s3.delete_bucket(Bucket=bucket)
                logger.info(f"Deleted bucket: {bucket}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete bucket {bucket}: {e}")
                return False
    
    # ==================== Object Operations ====================
    
    async def upload(
        self,
        bucket: str,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> str:
        """
        Upload an object.
        
        Args:
            bucket: Bucket name
            key: Object key
            data: File data
            content_type: MIME type
            metadata: Optional metadata
        
        Returns:
            Object URL
        """
        async with self.session.client("s3", **self._get_client_config()) as s3:
            if isinstance(data, bytes):
                data = io.BytesIO(data)
            
            extra_args = {
                "ContentType": content_type,
            }
            if metadata:
                extra_args["Metadata"] = metadata
            
            await s3.upload_fileobj(
                data,
                bucket,
                key,
                ExtraArgs=extra_args,
            )
            
            logger.debug(f"Uploaded {key} to {bucket}")
            return f"{self.settings.s3_endpoint}/{bucket}/{key}"
    
    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_path: str | Path,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Upload a file from disk."""
        file_path = Path(file_path)
        
        if content_type is None:
            import mimetypes
            content_type, _ = mimetypes.guess_type(str(file_path))
            content_type = content_type or "application/octet-stream"
        
        with open(file_path, "rb") as f:
            return await self.upload(bucket, key, f, content_type, metadata)
    
    async def download(self, bucket: str, key: str) -> bytes:
        """Download an object."""
        async with self.session.client("s3", **self._get_client_config()) as s3:
            response = await s3.get_object(Bucket=bucket, Key=key)
            data = await response["Body"].read()
            return data
    
    async def download_file(
        self,
        bucket: str,
        key: str,
        file_path: str | Path,
    ) -> Path:
        """Download an object to disk."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = await self.download(bucket, key)
        file_path.write_bytes(data)
        
        return file_path
    
    async def download_stream(
        self,
        bucket: str,
        key: str,
        chunk_size: int = 8192,
    ) -> AsyncGenerator[bytes, None]:
        """Stream download an object."""
        async with self.session.client("s3", **self._get_client_config()) as s3:
            response = await s3.get_object(Bucket=bucket, Key=key)
            
            async with response["Body"] as stream:
                while True:
                    chunk = await stream.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
    
    async def delete(self, bucket: str, key: str) -> bool:
        """Delete an object."""
        async with self.session.client("s3", **self._get_client_config()) as s3:
            try:
                await s3.delete_object(Bucket=bucket, Key=key)
                logger.debug(f"Deleted {key} from {bucket}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete {key}: {e}")
                return False
    
    async def delete_many(self, bucket: str, keys: list[str]) -> int:
        """Delete multiple objects."""
        async with self.session.client("s3", **self._get_client_config()) as s3:
            objects = [{"Key": k} for k in keys]
            
            response = await s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": objects},
            )
            
            deleted = len(response.get("Deleted", []))
            logger.debug(f"Deleted {deleted} objects from {bucket}")
            return deleted
    
    async def exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists."""
        async with self.session.client("s3", **self._get_client_config()) as s3:
            try:
                await s3.head_object(Bucket=bucket, Key=key)
                return True
            except Exception:
                return False
    
    async def get_metadata(
        self,
        bucket: str,
        key: str,
    ) -> Optional[dict[str, Any]]:
        """Get object metadata."""
        async with self.session.client("s3", **self._get_client_config()) as s3:
            try:
                response = await s3.head_object(Bucket=bucket, Key=key)
                return {
                    "content_type": response.get("ContentType"),
                    "content_length": response.get("ContentLength"),
                    "last_modified": response.get("LastModified"),
                    "etag": response.get("ETag"),
                    "metadata": response.get("Metadata", {}),
                }
            except Exception:
                return None
    
    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        delimiter: str = "",
        max_keys: int = 1000,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        List objects in a bucket.
        
        Args:
            bucket: Bucket name
            prefix: Filter by prefix
            delimiter: Group by delimiter
            max_keys: Maximum keys per request
        
        Yields:
            Object info dicts
        """
        async with self.session.client("s3", **self._get_client_config()) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            
            async for page in paginator.paginate(
                Bucket=bucket,
                Prefix=prefix,
                Delimiter=delimiter,
                PaginationConfig={"PageSize": max_keys},
            ):
                for obj in page.get("Contents", []):
                    yield {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                        "etag": obj["ETag"],
                    }
    
    # ==================== Presigned URLs ====================
    
    async def get_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str:
        """
        Generate a presigned URL.
        
        Args:
            bucket: Bucket name
            key: Object key
            expires_in: URL validity in seconds
            method: S3 method (get_object, put_object)
        
        Returns:
            Presigned URL
        """
        async with self.session.client("s3", **self._get_client_config()) as s3:
            url = await s3.generate_presigned_url(
                method,
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
    
    async def get_upload_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        content_type: str = "application/octet-stream",
    ) -> dict[str, str]:
        """
        Generate a presigned upload URL.
        
        Args:
            bucket: Bucket name
            key: Object key
            expires_in: URL validity
            content_type: Expected content type
        
        Returns:
            Dict with url and fields for form upload
        """
        async with self.session.client("s3", **self._get_client_config()) as s3:
            response = await s3.generate_presigned_post(
                bucket,
                key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                ],
                ExpiresIn=expires_in,
            )
            return response
    
    # ==================== Model Storage ====================
    
    async def store_model(
        self,
        model_id: str,
        model_data: bytes,
        metadata: dict[str, str],
        bucket: Optional[str] = None,
    ) -> str:
        """
        Store a model artifact.
        
        Args:
            model_id: Model identifier
            model_data: Serialized model
            metadata: Model metadata
            bucket: Optional bucket override
        
        Returns:
            Model storage URL
        """
        bucket = bucket or f"{self.config.default_bucket}-models"
        await self.create_bucket(bucket)
        
        key = f"models/{model_id}/model.bin"
        return await self.upload(
            bucket,
            key,
            model_data,
            content_type="application/octet-stream",
            metadata=metadata,
        )
    
    async def load_model(
        self,
        model_id: str,
        bucket: Optional[str] = None,
    ) -> Optional[bytes]:
        """Load a model artifact."""
        bucket = bucket or f"{self.config.default_bucket}-models"
        key = f"models/{model_id}/model.bin"
        
        if not await self.exists(bucket, key):
            return None
        
        return await self.download(bucket, key)
    
    # ==================== Lifecycle ====================
    
    async def health_check(self) -> bool:
        """Check storage connectivity."""
        try:
            await self.list_buckets()
            return True
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return False
    
    async def initialize(self) -> None:
        """Initialize default buckets."""
        buckets = [
            f"{self.config.default_bucket}-models",
            f"{self.config.default_bucket}-artifacts",
            f"{self.config.default_bucket}-evaluations",
            f"{self.config.default_bucket}-reports",
        ]
        
        for bucket in buckets:
            await self.create_bucket(bucket)


# Global storage instance
_storage_service: Optional[StorageService] = None


def get_storage() -> StorageService:
    """Get the global storage service."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


async def init_storage() -> StorageService:
    """Initialize and return the storage service."""
    storage = get_storage()
    await storage.initialize()
    return storage
