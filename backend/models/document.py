"""
文档模型
"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, ForeignKey
from typing import Optional

from common.orm import Base, TimestampMixin, BaseModelMixin


class Document(Base, TimestampMixin, BaseModelMixin):
    """
    文档模型
    继承 Base、TimestampMixin 和 BaseModelMixin
    """
    __tablename__ = "documents"

    knowledge_base_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, comment="知识库ID"
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="文件名")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="文件大小（字节）")
    file_type: Mapped[str] = mapped_column(String(100), nullable=False, comment="文件类型")
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="文件存储路径")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="processing", comment="处理状态: processing, completed, failed"
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="处理进度 (0-100)")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误信息")
    chunk_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="文档分块数量")

    def __repr__(self):
        return f"<Document(id={self.id}, file_name={self.file_name}, status={self.status})>"
