"""
文本提取模块 - 从不同格式的文档中提取文本
"""
import os
from pathlib import Path
from typing import Optional

from common.logger import get_logger

logger = get_logger(__name__)


class TextExtractor:
    """文本提取器"""

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        从文件中提取文本

        Args:
            file_path: 文件路径

        Returns:
            提取的文本内容

        Raises:
            ValueError: 不支持的文件类型
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.pdf':
            return TextExtractor._extract_from_pdf(file_path)
        elif file_ext == '.docx':
            return TextExtractor._extract_from_docx(file_path)
        elif file_ext in ['.txt', '.md']:
            return TextExtractor._extract_from_text_file(file_path)
        elif file_ext == '.doc':
            return TextExtractor._extract_from_doc(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """从 PDF 文件中提取文本"""
        try:
            import PyPDF2

            text = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text())

            return '\n'.join(text)
        except ImportError:
            logger.warning("PyPDF2 未安装，尝试使用 pdfplumber")
            return TextExtractor._extract_from_pdf_plumber(file_path)
        except Exception as e:
            logger.error(f"PDF 提取失败: {e}")
            return ""

    @staticmethod
    def _extract_from_pdf_plumber(file_path: str) -> str:
        """使用 pdfplumber 从 PDF 文件中提取文本"""
        try:
            import pdfplumber

            text = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text.append(page.extract_text() or "")

            return '\n'.join(text)
        except ImportError:
            logger.error("pdfplumber 未安装，无法提取 PDF 文本")
            return ""
        except Exception as e:
            logger.error(f"PDF 提取失败: {e}")
            return ""

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        """从 DOCX 文件中提取文本"""
        try:
            from docx import Document

            doc = Document(file_path)
            text = [para.text for para in doc.paragraphs]
            return '\n'.join(text)
        except ImportError:
            logger.error("python-docx 未安装，无法提取 DOCX 文本")
            return ""
        except Exception as e:
            logger.error(f"DOCX 提取失败: {e}")
            return ""

    @staticmethod
    def _extract_from_doc(file_path: str) -> str:
        """从 DOC 文件中提取文本（使用 antiword）"""
        try:
            import subprocess

            result = subprocess.run(
                ['antiword', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout
        except Exception as e:
            logger.error(f"DOC 提取失败: {e}")
            return ""

    @staticmethod
    def _extract_from_text_file(file_path: str) -> str:
        """从纯文本文件中提取文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"文本文件读取失败: {e}")
                return ""
        except Exception as e:
            logger.error(f"文本文件读取失败: {e}")
            return ""
