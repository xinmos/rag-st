"""知识库相关的请求和响应模型"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeBaseCreateRequest(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=200, description="知识库名称")
    description: str = Field("", min_length=0, max_length=5000, description="知识库描述")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "技术文档库",
                    "description": "存放技术相关的文档"
                }
            ]
        }
    }


class KnowledgeBaseUpdateRequest(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="知识库名称")
    description: Optional[str] = Field(None, min_length=0, max_length=5000, description="知识库描述")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "更新后的名称",
                    "description": "更新后的描述"
                }
            ]
        }
    }


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    description: str
    document_count: int
    created_at: datetime = Field(alias="create_time", serialization_alias="created_at")
    updated_at: datetime = Field(alias="create_time", serialization_alias="updated_at")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "技术文档库",
                    "description": "存放技术相关的文档",
                    "document_count": 10,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                }
            ]
        }
    }


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应"""
    total: int
    items: list[KnowledgeBaseResponse]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total": 1,
                    "items": [
                        {
                            "id": 1,
                            "name": "技术文档库",
                            "description": "存放技术相关的文档",
                            "document_count": 10,
                            "created_at": "2024-01-01T00:00:00",
                            "updated_at": "2024-01-01T00:00:00"
                        }
                    ]
                }
            ]
        }
    }


class KnowledgeBaseGetRequest(BaseModel):
    """获取知识库请求"""
    id: int = Field(..., description="知识库ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"id": 1}
            ]
        }
    }


class KnowledgeBaseDeleteRequest(BaseModel):
    """删除知识库请求"""
    id: int = Field(..., description="知识库ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"id": 1}
            ]
        }
    }


class KnowledgeBaseListRequest(BaseModel):
    """知识库列表请求"""
    page: int = Field(1, ge=1, description="页码")
    pageSize: int = Field(10, ge=1, le=100, description="每页数量")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"page": 1, "pageSize": 10}
            ]
        }
    }
