"""文档相关的请求和响应模型"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    knowledge_base_id: int
    file_name: str
    file_size: int
    file_type: str
    status: str
    progress: int = 0
    chunk_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(alias="create_time", serialization_alias="created_at")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "knowledge_base_id": 1,
                    "file_name": "document.pdf",
                    "file_size": 1024000,
                    "file_type": "application/pdf",
                    "status": "processing",
                    "progress": 50,
                    "chunk_count": None,
                    "error_message": None,
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
        }
    }


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    total: int
    items: list[DocumentResponse]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total": 1,
                    "items": [
                        {
                            "id": 1,
                            "knowledge_base_id": 1,
                            "file_name": "document.pdf",
                            "file_size": 1024000,
                            "file_type": "application/pdf",
                            "status": "completed",
                            "created_at": "2024-01-01T00:00:00"
                        }
                    ]
                }
            ]
        }
    }


class DocumentListRequest(BaseModel):
    """文档列表请求"""
    knowledge_base_id: int = Field(..., description="知识库ID")
    page: int = Field(1, ge=1, description="页码")
    pageSize: int = Field(10, ge=1, le=100, description="每页数量")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"knowledge_base_id": 1, "page": 1, "pageSize": 10}
            ]
        }
    }


class DocumentDeleteRequest(BaseModel):
    """删除文档请求"""
    knowledge_base_id: int = Field(..., description="知识库ID")
    document_id: int = Field(..., description="文档ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"knowledge_base_id": 1, "document_id": 1}
            ]
        }
    }


class ChatRequest(BaseModel):
    """聊天请求"""
    knowledge_base_id: int = Field(..., description="知识库ID")
    message: str = Field(..., min_length=1, description="用户消息")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "knowledge_base_id": 1,
                    "message": "什么是机器学习？"
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    sources: list[dict] = Field(default_factory=list, description="参考文档来源")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "机器学习是人工智能的一个分支...",
                    "sources": [
                        {"document_id": 1, "file_name": "AI入门.pdf", "chunk_id": 10}
                    ]
                }
            ]
        }
    }
