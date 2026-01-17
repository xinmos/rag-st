"""
MinIO 对象存储服务
"""
import io
from typing import Optional, Generator
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from common.config import settings
from common.logger import get_logger

logger = get_logger(__name__)

# 流式传输的块大小（8KB）
CHUNK_SIZE = 8192


class MinioService:
    """MinIO 对象存储服务"""

    def __init__(self):
        """初始化 MinIO 客户端"""
        self._client: Optional[Minio] = None
        self._bucket_name = settings.minio_bucket_name

    @property
    def client(self) -> Minio:
        """懒加载 MinIO 客户端"""
        if self._client is None:
            # 清理 endpoint，移除可能的协议和路径
            endpoint = settings.minio_endpoint.strip()
            # 移除协议前缀（http:// 或 https://）
            if endpoint.startswith('http://'):
                endpoint = endpoint[7:]
            elif endpoint.startswith('https://'):
                endpoint = endpoint[8:]
            # 移除路径部分（只保留 host:port）
            if '/' in endpoint:
                endpoint = endpoint.split('/')[0]

            self._client = Minio(
                endpoint=endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure
            )
            # 确保存储桶存在
            self._ensure_bucket_exists()
        return self._client

    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self._bucket_name):
                self.client.make_bucket(self._bucket_name)
                logger.info(f"✅ 创建 MinIO 存储桶: {self._bucket_name}")
            else:
                logger.info(f"📦 MinIO 存储桶已存在: {self._bucket_name}")
        except S3Error as e:
            logger.error(f"❌ MinIO 存储桶操作失败: {e}")
            raise

    def generate_object_name(self, knowledge_base_id: int, filename: str) -> str:
        """
        生成对象名称

        Args:
            knowledge_base_id: 知识库ID
            filename: 文件名

        Returns:
            str: 对象名称，格式为 knowledge_bases/{kb_id}/{filename}
        """
        return f"knowledge_bases/{knowledge_base_id}/{filename}"

    async def upload_file(
        self,
        knowledge_base_id: int,
        filename: str,
        file_data: bytes,
        content_type: str
    ) -> str:
        """
        上传文件到 MinIO

        Args:
            knowledge_base_id: 知识库ID
            filename: 文件名
            file_data: 文件数据
            content_type: 文件类型

        Returns:
            str: 对象名称

        Raises:
            S3Error: 上传失败
        """
        object_name = self.generate_object_name(knowledge_base_id, filename)

        try:
            # 将字节数据转换为 BytesIO
            file_stream = io.BytesIO(file_data)
            file_size = len(file_data)

            # 上传文件
            self.client.put_object(
                bucket_name=self._bucket_name,
                object_name=object_name,
                data=file_stream,
                length=file_size,
                content_type=content_type
            )

            logger.info(f"✅ 文件上传到 MinIO 成功: {object_name} ({file_size} bytes)")
            return object_name

        except S3Error as e:
            logger.error(f"❌ MinIO 上传文件失败: {filename}, 错误: {e}")
            raise

    async def download_file(self, object_name: str) -> bytes:
        """
        从 MinIO 下载文件（一次性读取到内存）

        注意：此方法将整个文件读入内存，仅适用于小文件。
        对于大文件，请使用 stream_file 方法。

        Args:
            object_name: 对象名称

        Returns:
            bytes: 文件数据

        Raises:
            S3Error: 下载失败
        """
        try:
            response = self.client.get_object(
                bucket_name=self._bucket_name,
                object_name=object_name
            )
            file_data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"✅ 从 MinIO 下载文件成功: {object_name} ({len(file_data)} bytes)")
            return file_data

        except S3Error as e:
            logger.error(f"❌ MinIO 下载文件失败: {object_name}, 错误: {e}")
            raise

    def stream_file(self, object_name: str) -> Generator[bytes, None, None]:
        """
        流式下载文件（适用于大文件）

        使用生成器逐块读取文件，避免一次性加载到内存。

        Args:
            object_name: 对象名称

        Yields:
            bytes: 文件数据块

        Raises:
            S3Error: 下载失败

        Example:
            >>> for chunk in minio_service.stream_file("path/to/file.pdf"):
            ...     # 处理每个数据块
            ...     pass
        """
        try:
            response = self.client.get_object(
                bucket_name=self._bucket_name,
                object_name=object_name
            )

            # 获取文件大小（用于日志）
            file_size = response.getheader('Content-Length')
            if file_size:
                file_size = int(file_size)
                logger.info(f"🔄 开始流式下载文件: {object_name} (大小: {file_size} bytes)")
            else:
                logger.info(f"🔄 开始流式下载文件: {object_name}")

            # 流式读取数据
            total_read = 0
            try:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    total_read += len(chunk)
                    yield chunk
            finally:
                # 确保关闭响应和释放连接
                response.close()
                response.release_conn()

            logger.info(f"✅ 流式下载完成: {object_name} (共 {total_read} bytes)")

        except S3Error as e:
            logger.error(f"❌ MinIO 流式下载失败: {object_name}, 错误: {e}")
            raise

    async def download_to_file(self, object_name: str, local_path: str) -> int:
        """
        流式下载文件到本地路径（适用于大文件）

        直接将 MinIO 文件流式下载到本地文件，避免将整个文件加载到内存。

        Args:
            object_name: MinIO 对象名称
            local_path: 本地文件路径

        Returns:
            int: 下载的字节数

        Raises:
            S3Error: 下载失败
            IOError: 文件写入失败

        Example:
            >>> await minio_service.download_to_file("path/to/file.pdf", "/tmp/file.pdf")
        """
        try:
            response = self.client.get_object(
                bucket_name=self._bucket_name,
                object_name=object_name
            )

            # 获取文件大小（用于日志）
            file_size = response.getheader('Content-Length')
            if file_size:
                file_size = int(file_size)
                logger.info(f"🔄 开始流式下载到文件: {object_name} -> {local_path} (大小: {file_size} bytes)")
            else:
                logger.info(f"🔄 开始流式下载到文件: {object_name} -> {local_path}")

            # 确保目标目录存在
            local_file_path = Path(local_path)
            local_file_path.parent.mkdir(parents=True, exist_ok=True)

            # 流式写入文件
            total_read = 0
            try:
                with open(local_path, 'wb') as f:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)
                        total_read += len(chunk)
            finally:
                # 确保关闭响应和释放连接
                response.close()
                response.release_conn()

            logger.info(f"✅ 流式下载到文件完成: {local_path} (共 {total_read} bytes)")
            return total_read

        except S3Error as e:
            logger.error(f"❌ MinIO 下载到文件失败: {object_name}, 错误: {e}")
            raise
        except IOError as e:
            logger.error(f"❌ 文件写入失败: {local_path}, 错误: {e}")
            raise

    async def delete_file(self, object_name: str) -> bool:
        """
        从 MinIO 删除文件

        Args:
            object_name: 对象名称

        Returns:
            bool: 是否删除成功

        Raises:
            S3Error: 删除失败
        """
        try:
            self.client.remove_object(
                bucket_name=self._bucket_name,
                object_name=object_name
            )
            logger.info(f"✅ 从 MinIO 删除文件成功: {object_name}")
            return True

        except S3Error as e:
            logger.error(f"❌ MinIO 删除文件失败: {object_name}, 错误: {e}")
            raise

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """
        生成预签名 URL，用于临时访问文件

        Args:
            object_name: 对象名称
            expires: 过期时间（秒），默认 1 小时

        Returns:
            str: 预签名 URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self._bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url

        except S3Error as e:
            logger.error(f"❌ 生成预签名 URL 失败: {object_name}, 错误: {e}")
            raise

    def get_file_url(self, object_name: str) -> str:
        """
        获取文件的公共访问 URL（如果存储桶是公开的）

        Args:
            object_name: 对象名称

        Returns:
            str: 文件 URL
        """
        # MinIO 的公共 URL 格式
        protocol = "https" if settings.minio_secure else "http"
        return f"{protocol}://{settings.minio_endpoint}/{self._bucket_name}/{object_name}"


# 全局 MinIO 服务实例
_minio_service: Optional[MinioService] = None


def get_minio_service() -> MinioService:
    """获取 MinIO 服务实例（单例）"""
    global _minio_service
    if _minio_service is None:
        _minio_service = MinioService()
    return _minio_service
