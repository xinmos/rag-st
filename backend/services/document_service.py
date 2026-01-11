import os
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select, func

from common.context import get_request_context
from common.logger import get_logger
from common.entity.schemas.document import (
    DocumentListRequest,
    DocumentResponse,
    DocumentListResponse,
)
from common.config import settings

logger = get_logger(__name__)


class DocumentService:
    """文档相关业务逻辑"""

    @staticmethod
    def get_upload_dir(knowledge_base_id: int) -> Path:
        """获取知识库文件上传目录"""
        upload_dir = Path(settings.upload_dir) / "knowledge_bases" / str(knowledge_base_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

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
        from models.document import Document
        from models.knowledge_base import KnowledgeBase

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

        # 生成安全的文件名
        file_ext = os.path.splitext(file.filename)[1]
        safe_filename = f"{int(asyncio.get_event_loop().time() * 1000)}{file_ext}"

        # 保存文件
        upload_dir = DocumentService.get_upload_dir(knowledge_base_id)
        file_path = upload_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        # 创建文档记录
        new_doc = await Document.create(
            knowledge_base_id=knowledge_base_id,
            file_name=file.filename,
            file_size=file_size,
            file_type=file.content_type or "application/octet-stream",
            file_path=str(file_path),
            status="processing",
            progress=0
        )

        logger.info(f"📄 文档上传成功: {file.filename} (ID: {new_doc.id}, 大小: {file_size} bytes)")

        # 异步处理文档（向量化）
        logger.info(f"🔄 启动后台处理任务: 文档ID={new_doc.id}")
        task = asyncio.create_task(
            DocumentService._process_document_async(new_doc.id, knowledge_base_id, str(file_path), file.filename)
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
    async def _process_document_async(document_id: int, knowledge_base_id: int, file_path: str, file_name: str):
        """
        异步处理文档（提取文本、分块、向量化）
        """
        from models.document import Document
        from processor import TextExtractor, TextChunker, get_embedding_service, get_vector_db_service
        from common.orm.db import AsyncSessionLocal
        from common import use_test_session

        # 创建新的 session 用于后台任务
        async with AsyncSessionLocal() as session:
            try:
                async with use_test_session(session):
                    logger.info(f"🚀 开始处理文档: {file_name} (ID: {document_id})")

                    # 更新进度: 10%
                    await Document.update_by_id(document_id, progress=10)
                    await session.commit()

                    # 1. 提取文本
                    logger.info(f"📖 [1/4] 正在提取文本: {file_name}")
                    text_extractor = TextExtractor()
                    text = text_extractor.extract_text(file_path)

                    if not text or len(text.strip()) < 10:
                        raise ValueError("提取的文本内容太少或为空")

                    text_length = len(text)
                    logger.info(f"✅ 文本提取成功: {text_length} 字符")

                    # 更新进度: 30%
                    await Document.update_by_id(document_id, progress=30)
                    await session.commit()

                    # 2. 文本分块
                    logger.info(f"✂️ [2/4] 正在分块文本: {file_name}")
                    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
                    chunks = chunker.chunk_text(text)

                    if not chunks:
                        raise ValueError("文本分块失败")

                    logger.info(f"✅ 文本分块完成: {len(chunks)} 个块")

                    # 更新进度: 50%
                    await Document.update_by_id(document_id, progress=50)
                    await session.commit()

                    # 3. 向量化
                    logger.info(f"🔢 [3/4] 正在生成向量嵌入: {file_name} ({len(chunks)} 个块)")
                    embedding_service = get_embedding_service()
                    chunk_texts = [chunk.text for chunk in chunks]

                    embeddings = embedding_service.encode(chunk_texts)

                    logger.info(f"✅ 向量嵌入生成完成: shape={embeddings.shape}")

                    # 更新进度: 70%
                    await Document.update_by_id(document_id, progress=70)
                    await session.commit()

                    # 4. 存储到向量数据库
                    logger.info(f"💾 [4/4] 正在存储到向量数据库: {file_name}")
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
        from models.document import Document

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
        from models.document import Document
        from processor import get_vector_db_service

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

        # 删除文件
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception as e:
                # 文件删除失败，继续删除数据库记录
                pass

        # 执行删除
        deleted = await Document.delete_by_id(document_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除文档失败"
            )

        return True
