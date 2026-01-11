"""
Embedding 服务 - 生成文本向量
支持 Sentence Transformer 和 Ollama 后端
"""
from typing import List, Union
import numpy as np

from common.config import settings
from common.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Embedding 服务，支持多种模型后端"""

    def __init__(self):
        self._model = None
        self._model_type = None  # 'sentence_transformer', 'ollama'

    def _load_model(self):
        """延迟加载模型"""
        if self._model is not None:
            return

        logger.info(f"加载 embedding 模型: {settings.embedding_model}")

        # 根据配置选择后端
        if settings.embedding_backend == "ollama" or "ollama/" in settings.embedding_model.lower():
            self._load_ollama_model()
        else:
            self._load_sentence_transformer_model()

    def _load_sentence_transformer_model(self):
        """加载 Sentence Transformer 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.embedding_model)
            self._model_type = 'sentence_transformer'
            logger.info("使用 sentence-transformers 后端")
        except ImportError:
            logger.error("sentence-transformers 未安装")
            raise ImportError(
                "请安装 sentence-transformers: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise

    def _load_ollama_model(self):
        """加载 Ollama Embedding 模型"""
        self._model_type = 'ollama'
        logger.info("使用 Ollama embedding 后端")

    def _encode_with_sentence_transformer(self, texts: Union[str, List[str]]) -> np.ndarray:
        """使用 Sentence Transformer 编码"""
        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]

        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        if single_input:
            return embeddings[0]
        return embeddings

    async def _encode_with_ollama(self, texts: Union[str, List[str]]) -> np.ndarray:
        """使用 Ollama 编码"""
        import httpx

        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]

        embeddings = []
        for text in texts:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{settings.ollama_base_url}/api/embeddings",
                        json={
                            "model": settings.embedding_model.replace("ollama/", ""),
                            "prompt": text
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    embedding = np.array(data["embedding"])
                    embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Ollama embedding 失败: {e}")
                raise

        embeddings_array = np.array(embeddings)
        # 归一化
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        embeddings_array = embeddings_array / norms

        if single_input:
            return embeddings_array[0]
        return embeddings_array

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        将文本编码为向量

        Args:
            texts: 单个文本或文本列表

        Returns:
            向量数组，形状为 (n, dimension) 或 (dimension,)
        """
        import asyncio

        if self._model is None:
            self._load_model()

        if self._model_type == 'ollama':
            # Ollama 是异步的，需要在事件循环中运行
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，使用 run_in_executor 在线程池中运行
                import concurrent.futures
                import threading
                result = [None]
                exception = [None]

                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            result[0] = new_loop.run_until_complete(self._encode_with_ollama(texts))
                        finally:
                            new_loop.close()
                    except Exception as e:
                        exception[0] = e

                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()

                if exception[0]:
                    raise exception[0]
                return result[0]
            except RuntimeError:
                # 如果没有事件循环，创建新的
                return asyncio.run(self._encode_with_ollama(texts))
        else:
            return self._encode_with_sentence_transformer(texts)

    @property
    def dimension(self) -> int:
        """获取向量维度"""
        return settings.embedding_dimension


# 全局单例
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """获取 embedding 服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
