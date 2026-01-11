from common.base_router import ApiRouter
from common.entity.base_response import BaseResponse
from common.entity.schemas.document import ChatRequest, ChatResponse

from services import RagService

# 默认所有路由需要认证
router = ApiRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("", response_model=BaseResponse[ChatResponse])
async def chat(request: ChatRequest):
    """
    基于知识库的问答

    - 需要认证
    - 使用 RAG 技术检索知识库内容并生成回答
    """
    result = await RagService.chat(
        knowledge_base_id=request.knowledge_base_id,
        message=request.message
    )
    return BaseResponse(code=0, message="success", data=result)
