"""
知识库模型
"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, select, func

from common.orm import Base, TimestampMixin, BaseModelMixin


class KnowledgeBase(Base, TimestampMixin, BaseModelMixin):
    """
    知识库模型
    继承 Base、TimestampMixin 和 BaseModelMixin
    - Base: SQLAlchemy 基础类
    - TimestampMixin: 自动包含 id 和 create_time 字段
    - BaseModelMixin: 提供增删改查类方法
    """
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="知识库名称")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", comment="知识库描述")

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name={self.name})>"

    async def document_count(self) -> int:
        """
        获取文档数量

        Returns:
            int: 文档数量
        """
        from models.document import Document

        session = self.get_session()
        stmt = select(func.count()).select_from(Document).where(
            Document.knowledge_base_id == self.id
        )
        result = await session.execute(stmt)
        return result.scalar() or 0
