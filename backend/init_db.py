"""数据库初始化脚本"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from common.config import settings
from common.orm.base_model import Base
from models.user import User
from models.knowledge_base import KnowledgeBase
from models.document import Document


async def init_db():
    """初始化数据库表"""
    engine = create_async_engine(settings.db_url, echo=True)

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("数据库表创建成功！")

    # 可选：创建一个测试用户
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # 检查是否已有用户
            from sqlalchemy import select, func
            result = await session.execute(select(func.count()).select_from(User))
            count = result.scalar()

            if count == 0:
                # 创建测试用户
                from common.utils import hash_password
                test_user = User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=hash_password("admin123")
                )
                session.add(test_user)
                await session.commit()
                print("测试用户创建成功！")
                print("用户名: admin")
                print("密码: admin123")
            else:
                print(f"数据库中已有 {count} 个用户，跳过创建测试用户")
        except Exception as e:
            await session.rollback()
            print(f"创建测试用户失败: {e}")
        finally:
            await session.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
