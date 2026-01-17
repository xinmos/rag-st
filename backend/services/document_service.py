import asyncio
import os
import tempfile
from pathlib import Path

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select, func

from common import use_test_session
from common.config import settings
from common.context import get_request_context
from common.entity.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
)
from common.logger import get_logger
from common.orm.db import AsyncSessionLocal
from models.document import Document
from models.knowledge_base import KnowledgeBase
from processor import TextExtractor, TextChunker, get_embedding_service
from processor import get_vector_db_service
from services.minio_service import get_minio_service

logger = get_logger(__name__)


class DocumentService:
    """文档相关业务逻辑"""

    @staticmethod
    async def upload_document(
        knowledge_base_id: int,
        file: UploadFile,
        file_content: bytes,
        file_size: int
    ) -> DocumentResponse:
        """
        上传文档

        Args:
            knowledge_base_id: 知识库ID
            file: 上传的文件
            file_content: 文件内容
            file_size: 文件大小

        Returns:
            DocumentResponse: 创建的文档信息
        """
        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        # 验证知识库是否存在
        kb = await KnowledgeBase.get_by_id(knowledge_base_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        # 生成唯一的对象名称
        file_ext = os.path.splitext(file.filename)[1]
        timestamp = int(asyncio.get_event_loop().time() * 1000)
        safe_filename = f"{timestamp}_{file.filename}"

        # 上传文件到 MinIO
        minio_service = get_minio_service()
        object_name = await minio_service.upload_file(
            knowledge_base_id=knowledge_base_id,
            filename=safe_filename,
            file_data=file_content,
            content_type=file.content_type or "application/octet-stream"
        )

        # 创建文档记录（file_path 存储 MinIO 对象名称）
        new_doc = await Document.create(
            knowledge_base_id=knowledge_base_id,
            file_name=file.filename,
            file_size=file_size,
            file_type=file.content_type or "application/octet-stream",
            file_path=object_name,
            status="processing",
            progress=0
        )

        logger.info(f"📄 文档上传成功: {file.filename} (ID: {new_doc.id}, 大小: {file_size} bytes)")

        # 异步处理文档（向量化）
        logger.info(f"🔄 启动后台处理任务: 文档ID={new_doc.id}")
        task = asyncio.create_task(
            DocumentService._process_document_async(new_doc.id, knowledge_base_id, object_name, file.filename)
        )
        # 添加错误处理，避免任务静默失败
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

        return DocumentResponse(
            id=new_doc.id,
            knowledge_base_id=new_doc.knowledge_base_id,
            file_name=new_doc.file_name,
            file_size=new_doc.file_size,
            file_type=new_doc.file_type,
            status=new_doc.status,
            progress=0,  # 初始进度
            create_time=new_doc.create_time,
        )

    @staticmethod
    async def _process_document_async(document_id: int, knowledge_base_id: int, object_name: str, file_name: str):
        """
        异步处理文档（提取文本、分块、向量化）
        """

        # 创建新的 session 用于后台任务
        async with AsyncSessionLocal() as session:
            # 临时文件路径（用于下载 MinIO 文件进行文本提取）
            temp_file_path = None
            try:
                async with use_test_session(session):
                    logger.info(f"🚀 开始处理文档: {file_name} (ID: {document_id})")

                    # 更新进度: 10%
                    await Document.update_by_id(document_id, progress=10)
                    await session.commit()

                    # 从 MinIO 流式下载文件到临时目录（避免将整个文件加载到内存）
                    logger.info(f"📥 [1/5] 正在下载文件: {file_name}")
                    minio_service = get_minio_service()

                    # 创建临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
                        temp_file_path = temp_file.name

                    # 流式下载到临时文件
                    downloaded_size = await minio_service.download_to_file(object_name, temp_file_path)

                    logger.info(f"✅ 文件下载成功: {downloaded_size} bytes")

                    # 更新进度: 20%
                    await Document.update_by_id(document_id, progress=20)
                    await session.commit()

                    # 1. 提取文本
                    logger.info(f"📖 [2/5] 正在提取文本: {file_name}")
                    text_extractor = TextExtractor()
                    text = text_extractor.extract_text(temp_file_path)

                    if not text or len(text.strip()) < 10:
                        raise ValueError("提取的文本内容太少或为空")

                    text_length = len(text)
                    logger.info(f"✅ 文本提取成功: {text_length} 字符")

                    # 更新进度: 40%
                    await Document.update_by_id(document_id, progress=40)
                    await session.commit()

                    # 2. 文本分块
                    logger.info(f"✂️ [3/5] 正在分块文本: {file_name}")
                    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
                    chunks = chunker.chunk_text(text)

                    if not chunks:
                        raise ValueError("文本分块失败")

                    logger.info(f"✅ 文本分块完成: {len(chunks)} 个块")

                    # 更新进度: 60%
                    await Document.update_by_id(document_id, progress=60)
                    await session.commit()

                    # 3. 向量化
                    logger.info(f"🔢 [4/5] 正在生成向量嵌入: {file_name} ({len(chunks)} 个块)")
                    embedding_service = get_embedding_service()
                    chunk_texts = [chunk.text for chunk in chunks]

                    embeddings = embedding_service.encode(chunk_texts)

                    logger.info(f"✅ 向量嵌入生成完成: shape={embeddings.shape}")

                    # 更新进度: 80%
                    await Document.update_by_id(document_id, progress=80)
                    await session.commit()

                    # 4. 存储到向量数据库
                    logger.info(f"💾 [5/5] 正在存储到向量数据库: {file_name}")
                    vector_db_service = get_vector_db_service()
                    chunk_data = [
                        (chunk.chunk_id, chunk.text, embedding.tolist())
                        for chunk, embedding in zip(chunks, embeddings)
                    ]
                    vector_db_service.insert_chunks(knowledge_base_id, document_id, chunk_data)

                    logger.info(f"✅ 向量存储完成: {len(chunk_data)} 个向量")

                    # 更新文档状态为完成
                    await Document.update_by_id(
                        document_id,
                        status="completed",
                        progress=100,
                        chunk_count=len(chunks)
                    )
                    await session.commit()

                    logger.info(f"🎉 文档处理完成: {file_name} (ID: {document_id})")

            except Exception as e:
                logger.error(f"❌ 文档处理失败: {file_name} (ID: {document_id}), 错误: {str(e)}", exc_info=True)
                async with use_test_session(session):
                    await Document.update_by_id(
                        document_id,
                        status="failed",
                        progress=0,
                        error_message=str(e)
                    )
                    await session.commit()
            finally:
                # 清理临时文件
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except Exception as e:
                        logger.warning(f"清理临时文件失败: {e}")
                await session.close()

    @staticmethod
    async def get_document_list(
        knowledge_base_id: int,
        page: int = 1,
        page_size: int = 10
    ) -> DocumentListResponse:
        """
        获取文档列表

        Args:
            knowledge_base_id: 知识库ID
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            DocumentListResponse: 文档列表和总数
        """
        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        session = Document.get_session()

        # 查询总数
        count_stmt = select(func.count()).select_from(Document).where(
            Document.knowledge_base_id == knowledge_base_id
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # 查询文档列表
        skip = (page - 1) * page_size
        stmt = select(Document).where(
            Document.knowledge_base_id == knowledge_base_id
        ).order_by(
            Document.create_time.desc()
        ).offset(skip).limit(page_size)

        result = await session.execute(stmt)
        documents = list(result.scalars().all())

        doc_responses = [
            DocumentResponse(
                id=doc.id,
                knowledge_base_id=doc.knowledge_base_id,
                file_name=doc.file_name,
                file_size=doc.file_size,
                file_type=doc.file_type,
                status=doc.status,
                progress=doc.progress,
                chunk_count=doc.chunk_count,
                error_message=doc.error_message,
                create_time=doc.create_time,
            )
            for doc in documents
        ]

        return DocumentListResponse(total=total, items=doc_responses)

    @staticmethod
    async def delete_document(knowledge_base_id: int, document_id: int) -> bool:
        """
        删除文档

        Args:
            knowledge_base_id: 知识库ID
            document_id: 文档ID

        Returns:
            bool: 是否删除成功

        Raises:
            HTTPException: 文档不存在或删除失败
        """
        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        # 检查文档是否存在
        doc = await Document.get_by_id(document_id)
        if not doc or doc.knowledge_base_id != knowledge_base_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )

        # 删除向量数据
        try:
            vector_db_service = get_vector_db_service()
            vector_db_service.delete_document(knowledge_base_id, document_id)
        except Exception as e:
            # 向量删除失败，记录日志但继续
            from common.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"删除文档向量失败: {e}")

        # 删除 MinIO 中的文件
        if doc.file_path:
            try:
                minio_service = get_minio_service()
                await minio_service.delete_file(doc.file_path)
                logger.info(f"✅ 从 MinIO 删除文件成功: {doc.file_path}")
            except Exception as e:
                # 文件删除失败，记录日志但继续删除数据库记录
                logger.warning(f"MinIO 文件删除失败: {e}")

        # 执行删除
        deleted = await Document.delete_by_id(document_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除文档失败"
            )

        return True
