from datetime import datetime
from typing import Optional, List, Any, TypeVar
from sqlalchemy import Integer, DateTime, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from common.context import get_request_context, get_test_session

# 定义泛型类型
ModelType = TypeVar('ModelType', bound='Base')


class Base(DeclarativeBase):
    """SQLAlchemy 基础模型类，所有表模型都继承此类"""
    pass


class TimestampMixin:
    """时间戳混入类，提供 id 和 create_time 字段"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    create_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )


class BaseModelMixin:
    """
    基础模型混入类，提供通用的增删改查类方法
    所有业务模型类应该继承此类，就可以直接使用 User.create(), User.get_by_id() 等方法
    
    在测试脚本中使用时，请使用 use_test_session 上下文管理器：
        async with use_test_session(session):
            user = await User.create(username="test")
    """
    
    @classmethod
    def get_session(cls) -> AsyncSession:
        """
        获取数据库会话
        优先从测试 session 上下文获取（用于测试脚本），否则从请求上下文获取
        
        Returns:
            数据库会话
            
        Raises:
            RuntimeError: 如果无法获取数据库会话
        """
        # 优先从测试 session 上下文获取（用于测试脚本）
        test_session = get_test_session()
        if test_session is not None:
            return test_session
        
        # 从请求上下文获取
        ctx = get_request_context()
        if ctx.session is None:
            raise RuntimeError(
                "无法获取数据库会话，请确保在请求上下文中使用，"
                "或者在测试脚本中使用 use_test_session 上下文管理器，例如：\n"
                "    async with use_test_session(session):\n"
                "        user = await User.create(username='test')"
            )
        return ctx.session
    
    @classmethod
    async def create(cls, **kwargs):
        """
        创建新记录
        
        Args:
            **kwargs: 模型字段的键值对
            
        Returns:
            创建的模型实例
        """
        session = cls.get_session()
        instance = cls(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance
    
    @classmethod
    async def get_by_id(cls, id: int):
        """
        根据 ID 获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            模型实例，如果不存在则返回 None
        """
        session = cls.get_session()
        result = await session.get(cls, id)
        return result
    
    @classmethod
    async def get_all(
        cls,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None
    ) -> List:
        """
        获取所有记录（支持分页和排序）
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            order_by: 排序字段，默认为 create_time 降序
            
        Returns:
            模型实例列表
        """
        session = cls.get_session()
        query = select(cls)
        
        # 默认按创建时间降序排序
        if order_by is None:
            if hasattr(cls, 'create_time'):
                order_by = cls.create_time.desc()
            else:
                order_by = None
        
        if order_by is not None:
            query = query.order_by(order_by)
        
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_filter(cls, **filters) -> List:
        """
        根据条件过滤获取记录

        Args:
            **filters: 过滤条件，键为字段名，值为过滤值

        Returns:
            符合条件的模型实例列表
        """
        session = cls.get_session()
        query = select(cls)

        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.where(getattr(cls, key) == value)

        # 默认按创建时间降序排序
        if hasattr(cls, 'create_time'):
            query = query.order_by(cls.create_time.desc())

        result = await session.execute(query)
        # 使用 scalars() 获取结果，避免懒加载问题
        return list(result.scalars().all())
    
    @classmethod
    async def update_by_id(cls, id: int, **kwargs):
        """
        根据 ID 更新记录
        
        Args:
            id: 记录ID
            **kwargs: 要更新的字段键值对
            
        Returns:
            更新后的模型实例，如果不存在则返回 None
        """
        session = cls.get_session()
        instance = await cls.get_by_id(id)
        if instance is None:
            return None
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        await session.flush()
        await session.refresh(instance)
        return instance
    
    @classmethod
    async def delete_by_id(cls, id: int) -> bool:
        """
        根据 ID 删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            如果删除成功返回 True，如果记录不存在返回 False
        """
        session = cls.get_session()
        instance = await cls.get_by_id(id)
        if instance is None:
            return False
        
        await session.delete(instance)
        await session.flush()
        return True
    
    @classmethod
    async def count(cls, **filters) -> int:
        """
        统计符合条件的记录数
        
        Args:
            **filters: 过滤条件
            
        Returns:
            记录数
        """
        session = cls.get_session()
        query = select(func.count()).select_from(cls)
        
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.where(getattr(cls, key) == value)
        
        result = await session.execute(query)
        return result.scalar() or 0
    
    @classmethod
    async def exists(cls, id: int) -> bool:
        """
        检查记录是否存在
        
        Args:
            id: 记录ID
            
        Returns:
            如果存在返回 True，否则返回 False
        """
        instance = await cls.get_by_id(id)
        return instance is not None
