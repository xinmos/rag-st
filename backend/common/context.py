import contextvars
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


class RequestContext:
    """请求上下文数据类"""
    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        user_id: Optional[int] = None,
        **kwargs
    ):
        self.session = session
        self.user_id = user_id
        # 可以存储其他自定义信息
        for key, value in kwargs.items():
            setattr(self, key, value)


# 上下文变量：保存当前请求的上下文信息
request_context: contextvars.ContextVar[RequestContext] = contextvars.ContextVar(
    "request_context",
    default=RequestContext()
)

# 测试用的 session 上下文变量（用于测试脚本）
test_session_context: contextvars.ContextVar[Optional[AsyncSession]] = contextvars.ContextVar(
    "test_session",
    default=None
)


def get_request_context() -> RequestContext:
    """获取当前请求上下文"""
    return request_context.get()


def set_request_context(ctx: RequestContext) -> contextvars.Token:
    """设置请求上下文"""
    return request_context.set(ctx)


def reset_request_context(token: contextvars.Token) -> None:
    """重置请求上下文"""
    request_context.reset(token)


def get_test_session() -> Optional[AsyncSession]:
    """获取测试用的 session（用于测试脚本）"""
    return test_session_context.get()


@asynccontextmanager
async def use_test_session(session: AsyncSession):
    """
    上下文管理器：在测试脚本中使用指定的 session
    
    使用示例：
        async with use_test_session(session):
            user = await User.create(username="test")
            user = await User.get_by_id(1)
    """
    token = test_session_context.set(session)
    try:
        yield session
    finally:
        test_session_context.reset(token)
