from fastapi import HTTPException, status

from common.context import get_request_context
from common.entity.schemas.knowledge_base import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseUpdateRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
)


class KnowledgeBaseService:
    """知识库相关业务逻辑"""

    @staticmethod
    async def create_kb(request: KnowledgeBaseCreateRequest) -> KnowledgeBaseResponse:
        """
        创建知识库

        Args:
            request: 知识库创建请求

        Returns:
            KnowledgeBaseResponse: 创建的知识库信息
        """
        from models.knowledge_base import KnowledgeBase

        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        # 创建知识库
        new_kb = await KnowledgeBase.create(
            name=request.name,
            description=request.description or ""
        )

        # 获取文档数量
        doc_count = await new_kb.document_count()

        return KnowledgeBaseResponse(
            id=new_kb.id,
            name=new_kb.name,
            description=new_kb.description,
            document_count=doc_count,
            create_time=new_kb.create_time,
        )

    @staticmethod
    async def get_kb_list(page: int = 1, page_size: int = 10) -> KnowledgeBaseListResponse:
        """
        获取知识库列表
        支持分页

        Args:
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            KnowledgeBaseListResponse: 知识库列表和总数
        """
        from models.knowledge_base import KnowledgeBase

        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        skip = (page - 1) * page_size
        kbs = await KnowledgeBase.get_all(skip=skip, limit=page_size)
        total = await KnowledgeBase.count()

        # 获取每个知识库的文档数量
        kb_responses = []
        for kb in kbs:
            doc_count = await kb.document_count()
            kb_responses.append(
                KnowledgeBaseResponse(
                    id=kb.id,
                    name=kb.name,
                    description=kb.description,
                    document_count=doc_count,
                    create_time=kb.create_time,
                )
            )

        return KnowledgeBaseListResponse(total=total, items=kb_responses)

    @staticmethod
    async def get_kb(kb_id: int) -> KnowledgeBaseResponse:
        """
        获取单个知识库

        Args:
            kb_id: 知识库ID

        Returns:
            KnowledgeBaseResponse: 知识库信息

        Raises:
            HTTPException: 知识库不存在
        """
        from models.knowledge_base import KnowledgeBase

        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        kb = await KnowledgeBase.get_by_id(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        # 获取文档数量
        doc_count = await kb.document_count()

        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=doc_count,
            create_time=kb.create_time,
        )

    @staticmethod
    async def update_kb(kb_id: int, request: KnowledgeBaseUpdateRequest) -> KnowledgeBaseResponse:
        """
        更新知识库

        Args:
            kb_id: 知识库ID
            request: 知识库更新请求

        Returns:
            KnowledgeBaseResponse: 更新后的知识库信息

        Raises:
            HTTPException: 知识库不存在
        """
        from models.knowledge_base import KnowledgeBase

        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        # 检查知识库是否存在
        kb = await KnowledgeBase.get_by_id(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        # 准备更新数据
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description

        # 执行更新
        if update_data:
            updated_kb = await KnowledgeBase.update_by_id(kb_id, **update_data)
            doc_count = await updated_kb.document_count()
            return KnowledgeBaseResponse(
                id=updated_kb.id,
                name=updated_kb.name,
                description=updated_kb.description,
                document_count=doc_count,
                create_time=updated_kb.create_time,
            )

        # 如果没有需要更新的字段
        doc_count = await kb.document_count()
        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=doc_count,
            create_time=kb.create_time,
        )

    @staticmethod
    async def delete_kb(kb_id: int) -> bool:
        """
        删除知识库

        Args:
            kb_id: 知识库ID

        Returns:
            bool: 是否删除成功

        Raises:
            HTTPException: 知识库不存在或删除失败
        """
        from models.knowledge_base import KnowledgeBase
        from processor import get_vector_db_service

        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        # 检查知识库是否存在
        kb = await KnowledgeBase.get_by_id(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        # 删除向量数据
        try:
            vector_db_service = get_vector_db_service()
            vector_db_service.delete_knowledge_base(kb_id)
        except Exception as e:
            # 向量删除失败，记录日志但继续
            from common.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"删除知识库向量失败: {e}")

        # 执行删除
        deleted = await KnowledgeBase.delete_by_id(kb_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除知识库失败"
            )

        return True
