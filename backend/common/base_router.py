from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.config import settings
from common.context import (
    RequestContext,
    reset_request_context,
    set_request_context,
)
from common.orm.db import AsyncSessionLocal

# 使用 auto_error=False 让认证变成可选的
security = HTTPBearer(auto_error=False)


async def init_request_context(request: Request) -> RequestContext:
    """
    FastAPI 依赖：初始化请求上下文
    创建数据库 session 并存储到上下文中，同时可以存储其他基本信息
    """
    session = AsyncSessionLocal()

    # 创建请求上下文，包含 session 和基本信息
    ctx = RequestContext(
        session=session,
        user_id=None,  # 如果不需要认证，可以设为 None
        path=request.url.path,
        method=request.method,
    )

    token = set_request_context(ctx)
    try:
        yield ctx
    finally:
        try:
            await session.commit()
        except Exception:
            await session.rollback()
        await session.close()
        reset_request_context(token)


async def get_current_user(
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ctx: RequestContext = Depends(init_request_context)
) -> Optional[int]:
    """
    解析 JWT，获取当前用户 ID
    同时将 user_id 存储到请求上下文中
    
    如果 cred 为 None（没有提供 token），返回 None 而不是抛出异常
    这样可以在路由级别决定是否需要强制认证
    """
    if cred is None:
        return None
    
    token = cred.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        user_id: int = int(payload["sub"])
        
        # 将 user_id 存储到上下文中
        ctx.user_id = user_id
        
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token 无效")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token 解析失败: {str(e)}")


async def require_auth(
    user_id: Optional[int] = Depends(get_current_user)
) -> int:
    """
    强制要求认证的依赖
    如果没有提供有效的 token，会抛出 401 错误
    """
    if user_id is None:
        raise HTTPException(status_code=401, detail="需要认证")
    return user_id


# 导出用于单个路由跳过认证的依赖列表
# 只包含上下文初始化，不包含认证
NO_AUTH = [Depends(init_request_context)]


class ApiRouter(APIRouter):
    """
    自定义 API Router，用于初始化请求上下文
    
    所有路由自动：
    1. 注入 init_request_context（创建数据库 session 并存储到上下文）
    2. 可选：注入 require_auth（如果 auth=True，强制要求认证）
    
    使用方式：
    - router = ApiRouter()  # 默认需要认证
    - router = ApiRouter(auth=True)  # 需要认证（默认）
    - router = ApiRouter(auth=False)  # 整个 router 都不需要认证
    
    单个路由跳过认证：
    - @router.get("/public", dependencies=NO_AUTH)  # 这个路由不需要认证，完全覆盖 router 依赖
    - @router.get("/private")  # 这个路由需要认证（如果 router auth=True）
    """
    
    def __init__(self, *, auth: bool = True, **kwargs):
        # 默认依赖：初始化请求上下文（包含 session）
        self._default_deps = [Depends(init_request_context)]
        
        # 如果需要认证，添加强制认证依赖
        if auth:
            self._default_deps.append(Depends(require_auth))
        
        kwargs.setdefault("dependencies", self._default_deps)
        super().__init__(**kwargs)
    
    def add_api_route(self, path: str, endpoint, dependencies=None, **kwargs):
        """
        重写路由添加方法，支持完全覆盖依赖
        如果 dependencies 是 NO_AUTH，则完全替换 router 的默认依赖
        """
        # 检查是否是 NO_AUTH（只检查对象引用，最简单直接）
        if dependencies is NO_AUTH:
            # 临时清空 router 的依赖，避免 FastAPI 合并依赖
            original_deps = self.dependencies.copy() if self.dependencies else []
            self.dependencies = []
            try:
                return super().add_api_route(path, endpoint, dependencies=NO_AUTH, **kwargs)
            finally:
                self.dependencies = original_deps
        
        # 默认行为：使用 FastAPI 的依赖合并机制
        return super().add_api_route(path, endpoint, dependencies=dependencies, **kwargs)