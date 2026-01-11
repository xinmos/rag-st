from common.base_router import NO_AUTH, ApiRouter
from common.entity.base_response import BaseResponse
from common.entity.schemas.knowledge_base import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseListRequest,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdateRequest,
)
from services import KnowledgeBaseService

# 默认所有路由需要认证
router = ApiRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])


@router.post("/list", response_model=BaseResponse[KnowledgeBaseListResponse])
async def get_kb_list(request: KnowledgeBaseListRequest):
    """
    获取知识库列表

    - 需要认证
    - 支持分页
    """
    result = await KnowledgeBaseService.get_kb_list(
        page=request.page, page_size=request.pageSize
    )
    return BaseResponse(code=0, message="获取知识库列表成功", data=result)


@router.post("/get", response_model=BaseResponse[KnowledgeBaseResponse])
async def get_kb(id: int):
    """
    获取单个知识库

    - 需要认证
    - 参数: id (query parameter)
    """
    result = await KnowledgeBaseService.get_kb(id)
    return BaseResponse(code=0, message="获取知识库成功", data=result)


@router.post("/create", response_model=BaseResponse[KnowledgeBaseResponse])
async def create_kb(request: KnowledgeBaseCreateRequest):
    """
    创建知识库

    - 需要认证
    - 知识库名称不能为空
    """
    result = await KnowledgeBaseService.create_kb(request)
    return BaseResponse(code=0, message="创建知识库成功", data=result)


@router.post("/update", response_model=BaseResponse[KnowledgeBaseResponse])
async def update_kb(id: int, request: KnowledgeBaseUpdateRequest):
    """
    更新知识库

    - 需要认证
    - 参数: id (query parameter)
    """
    result = await KnowledgeBaseService.update_kb(id, request)
    return BaseResponse(code=0, message="更新知识库成功", data=result)


@router.post("/delete", response_model=BaseResponse[dict])
async def delete_kb(id: int):
    """
    删除知识库

    - 需要认证
    - 参数: id (query parameter)
    """
    await KnowledgeBaseService.delete_kb(id)
    return BaseResponse(code=0, message="删除知识库成功", data={"deleted": True})
