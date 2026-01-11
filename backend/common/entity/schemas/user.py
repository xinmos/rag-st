"""用户相关的请求和响应模型"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "test_user",
                    "email": "test@example.com",
                    "password": "password123"
                }
            ]
        }
    }


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="密码")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "updated_user",
                    "email": "updated@example.com"
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    create_time: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "username": "test_user",
                    "email": "test@example.com",
                    "create_time": "2024-01-01T00:00:00"
                }
            ]
        }
    }


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    items: list[UserResponse]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total": 1,
                    "items": [
                        {
                            "id": 1,
                            "username": "test_user",
                            "email": "test@example.com",
                            "create_time": "2024-01-01T00:00:00"
                        }
                    ]
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "test_user",
                    "password": "password123"
                }
            ]
        }
    }


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user": {
                        "id": 1,
                        "username": "test_user",
                        "email": "test@example.com",
                        "create_time": "2024-01-01T00:00:00"
                    }
                }
            ]
        }
    }


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_password": "oldpassword123",
                    "new_password": "newpassword123"
                }
            ]
        }
    }


class UpdateProfileRequest(BaseModel):
    """更新个人信息请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "updated_user",
                    "email": "updated@example.com"
                }
            ]
        }
    }
