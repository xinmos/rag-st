from fastapi import File, UploadFile, Form

from common.base_router import NO_AUTH, ApiRouter
from common.entity.base_response import BaseResponse
from common.entity.schemas.document import (
    DocumentListRequest,
    DocumentListResponse,
    DocumentResponse,
    DocumentDeleteRequest,
)

from services import DocumentService

# 默认所有路由需要认证
router = ApiRouter(prefix="/api/v1/document", tags=["document"])


@router.post("/list", response_model=BaseResponse[DocumentListResponse])
async def get_document_list(request: DocumentListRequest):
    """
    获取文档列表

    - 需要认证
    - 支持分页
    """
    result = await DocumentService.get_document_list(
        knowledge_base_id=request.knowledge_base_id,
        page=request.page,
        page_size=request.pageSize
    )
    return BaseResponse(code=0, message="获取文档列表成功", data=result)


@router.post("/upload", response_model=BaseResponse[DocumentResponse])
async def upload_document(
    knowledge_base_id: int = Form(...),
    file: UploadFile = File(...),
):
    """
    上传文档

    - 需要认证
    - 支持的文件类型: .pdf, .doc, .docx, .txt, .md
    - 文档会在后台异步处理（提取文本、分块、向量化）
    """
    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)

    # 验证文件类型
    allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.md'}
    file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        return BaseResponse(
            code=400,
            message=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_extensions)}",
            data=None
        )

    result = await DocumentService.upload_document(
        knowledge_base_id=knowledge_base_id,
        file=file,
        file_content=file_content,
        file_size=file_size
    )
    return BaseResponse(code=0, message="上传文档成功，正在处理中", data=result)


@router.post("/delete", response_model=BaseResponse[dict])
async def delete_document(knowledge_base_id: int, document_id: int):
    """
    删除文档

    - 需要认证
    - 参数: knowledge_base_id, document_id (query parameters)
    """
    await DocumentService.delete_document(knowledge_base_id, document_id)
    return BaseResponse(code=0, message="删除文档成功", data={"deleted": True})
