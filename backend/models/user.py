"""
用户模型示例
展示如何使用 Base、TimestampMixin 和 BaseModelMixin 创建模型
"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, select

from common.orm import Base, TimestampMixin, BaseModelMixin


class User(Base, TimestampMixin, BaseModelMixin):
    """
    用户模型
    继承 Base、TimestampMixin 和 BaseModelMixin
    - Base: SQLAlchemy 基础类
    - TimestampMixin: 自动包含 id 和 create_time 字段
    - BaseModelMixin: 提供增删改查类方法，可以直接使用 User.create(), User.get_by_id() 等
    """
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户名")
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="邮箱")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    @classmethod
    async def get_by_username(cls, username: str):
        stmt = select(cls).where(cls.username == username)
        res = cls.get_session().execute(stmt)
        return res.scalar_one_or_none()
