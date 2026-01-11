from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from contextlib import asynccontextmanager

from common.config import settings

# 创建异步引擎
# SQLite 使用 aiosqlite 驱动
engine = create_async_engine(
    settings.db_url,
    # SQLite 不需要连接池，但可以设置一些参数
    pool_pre_ping=True,
    echo=settings.debug,  # 调试模式下打印 SQL
    connect_args={"check_same_thread": False} if "sqlite" in settings.db_url else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db_session():
    """
    获取数据库会话的上下文管理器

    用法:
        async with get_db_session() as session:
            # 使用 session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()