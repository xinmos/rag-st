"""
文本分块模块 - 将长文本分成小块以便于向量化和检索
"""
import re
from typing import List
from dataclasses import dataclass

from common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TextChunk:
    """文本块"""
    text: str
    chunk_id: int
    start_pos: int
    end_pos: int


class TextChunker:
    """文本分块器"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n\n"
    ):
        """
        初始化文本分块器

        Args:
            chunk_size: 每个块的最大字符数
            chunk_overlap: 块之间的重叠字符数
            separator: 分隔符，优先按分隔符切分
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        将文本分成块

        Args:
            text: 输入文本

        Returns:
            文本块列表
        """
        if not text or not text.strip():
            return []

        # 清理文本
        text = self._clean_text(text)

        # 按分隔符切分
        paragraphs = [p.strip() for p in text.split(self.separator) if p.strip()]

        chunks = []
        current_chunk = ""
        chunk_id = 0
        start_pos = 0

        for para in paragraphs:
            # 如果单个段落超过块大小，需要切分
            if len(para) > self.chunk_size:
                # 保存当前块
                if current_chunk:
                    chunks.append(TextChunk(
                        text=current_chunk.strip(),
                        chunk_id=chunk_id,
                        start_pos=start_pos,
                        end_pos=start_pos + len(current_chunk)
                    ))
                    chunk_id += 1
                    start_pos += len(current_chunk) - self.chunk_overlap
                    current_chunk = ""

                # 切分长段落
                sub_chunks = self._split_long_text(para)
                for sub_chunk in sub_chunks:
                    chunks.append(TextChunk(
                        text=sub_chunk,
                        chunk_id=chunk_id,
                        start_pos=start_pos,
                        end_pos=start_pos + len(sub_chunk)
                    ))
                    chunk_id += 1
                    start_pos += len(sub_chunk) - self.chunk_overlap
            else:
                # 检查添加这个段落后是否会超过块大小
                if len(current_chunk) + len(para) + len(self.separator) <= self.chunk_size:
                    if current_chunk:
                        current_chunk += self.separator + para
                    else:
                        current_chunk = para
                else:
                    # 保存当前块，开始新块
                    if current_chunk:
                        chunks.append(TextChunk(
                            text=current_chunk.strip(),
                            chunk_id=chunk_id,
                            start_pos=start_pos,
                            end_pos=start_pos + len(current_chunk)
                        ))
                        chunk_id += 1
                        start_pos += len(current_chunk) - self.chunk_overlap

                    # 添加重叠部分
                    if self.chunk_overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + self.separator + para
                    else:
                        current_chunk = para

        # 添加最后一个块
        if current_chunk:
            chunks.append(TextChunk(
                text=current_chunk.strip(),
                chunk_id=chunk_id,
                start_pos=start_pos,
                end_pos=start_pos + len(current_chunk)
            ))

        logger.info(f"文本分块完成: {len(chunks)} 个块")
        return chunks

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 移除行首行尾空格
        text = '\n'.join(line.strip() for line in text.split('\n'))
        return text

    def _split_long_text(self, text: str) -> List[str]:
        """切分过长的文本"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            if end >= len(text):
                chunks.append(text[start:].strip())
                break

            # 尝试在句子边界切分
            chunk = text[start:end]

            # 查找最后一个句号、问号或感叹号
            for punct in ['。', '！', '？', '.', '!', '?']:
                last_punct = chunk.rfind(punct)
                if last_punct > self.chunk_size // 2:
                    end = start + last_punct + 1
                    chunk = text[start:end]
                    break

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap if self.chunk_overlap > 0 else end

        return chunks
