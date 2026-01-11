"""
Chroma 向量数据库服务
本地文件向量数据库，无需额外部署
"""
from typing import List, Dict, Tuple, Optional
import uuid

from common.config import settings
from common.logger import get_logger

logger = get_logger(__name__)


class ChromaService:
    """Chroma 向量数据库服务"""

    def __init__(self):
        self._client = None
        self._collections = {}  # 知识库ID -> collection

    def _get_client(self):
        """获取 Chroma 客户端"""
        if self._client is not None:
            return self._client

        try:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"Chroma 客户端初始化成功，存储目录: {settings.chroma_persist_directory}")
            return self._client
        except ImportError:
            logger.error("chromadb 未安装")
            raise ImportError(
                "请安装 chromadb: pip install chromadb"
            )
        except Exception as e:
            logger.error(f"Chroma 客户端初始化失败: {e}")
            raise

    def _get_collection_name(self, knowledge_base_id: int) -> str:
        """获取集合名称"""
        return f"kb_{knowledge_base_id}"

    def _get_or_create_collection(self, knowledge_base_id: int):
        """获取或创建集合"""
        if knowledge_base_id in self._collections:
            return self._collections[knowledge_base_id]

        client = self._get_client()
        collection_name = self._get_collection_name(knowledge_base_id)

        try:
            # 尝试获取现有集合
            collection = client.get_collection(name=collection_name)
            logger.info(f"使用现有集合: {collection_name}")
        except Exception:
            # 集合不存在，创建新集合
            collection = client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"创建新集合: {collection_name}")

        self._collections[knowledge_base_id] = collection
        return collection

    def insert_chunks(
        self,
        knowledge_base_id: int,
        document_id: int,
        chunks: List[Tuple[int, str, list]]
    ):
        """
        插入文档块

        Args:
            knowledge_base_id: 知识库ID
            document_id: 文档ID
            chunks: (chunk_id, text, embedding) 元组列表
        """
        collection = self._get_or_create_collection(knowledge_base_id)

        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for chunk_id, text, embedding in chunks:
            # 生成唯一 ID
            unique_id = f"doc_{document_id}_chunk_{chunk_id}"
            ids.append(unique_id)
            embeddings.append(embedding)
            metadatas.append({
                "knowledge_base_id": str(knowledge_base_id),
                "document_id": str(document_id),
                "chunk_id": str(chunk_id)
            })
            documents.append(text)

        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"成功插入 {len(chunks)} 个文档块到知识库 {knowledge_base_id}")
        except Exception as e:
            logger.error(f"插入文档块失败: {e}")
            raise

    def search(
        self,
        knowledge_base_id: int,
        query_embedding: list,
        top_k: int = 5
    ) -> List[Dict]:
        """
        向量搜索

        Args:
            knowledge_base_id: 知识库ID
            query_embedding: 查询向量
            top_k: 返回结果数量

        Returns:
            搜索结果列表
        """
        collection = self._get_or_create_collection(knowledge_base_id)

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            # 格式化结果
            formatted_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "text": results['documents'][0][i] if results['documents'] else "",
                        "document_id": int(results['metadatas'][0][i]['document_id']),
                        "chunk_id": int(results['metadatas'][0][i]['chunk_id']),
                        "score": 1.0 - results['distances'][0][i] if results.get('distances') else 0.0,
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise

    def delete_document(self, knowledge_base_id: int, document_id: int):
        """
        删除文档的所有向量

        Args:
            knowledge_base_id: 知识库ID
            document_id: 文档ID
        """
        collection = self._get_or_create_collection(knowledge_base_id)

        try:
            # 获取该文档的所有 chunk ID
            results = collection.get(
                where={"document_id": str(document_id)}
            )

            if results['ids']:
                collection.delete(ids=results['ids'])
                logger.info(f"成功删除文档 {document_id} 的 {len(results['ids'])} 个向量")
            else:
                logger.info(f"文档 {document_id} 没有找到向量数据")

        except Exception as e:
            logger.error(f"删除文档向量失败: {e}")
            raise

    def delete_knowledge_base(self, knowledge_base_id: int):
        """
        删除整个知识库的向量

        Args:
            knowledge_base_id: 知识库ID
        """
        client = self._get_client()
        collection_name = self._get_collection_name(knowledge_base_id)

        try:
            client.delete_collection(name=collection_name)
            if knowledge_base_id in self._collections:
                del self._collections[knowledge_base_id]
            logger.info(f"成功删除知识库 {knowledge_base_id} 的集合")
        except Exception as e:
            logger.error(f"删除知识库集合失败: {e}")
            raise

    def get_collection_stats(self, knowledge_base_id: int) -> Dict:
        """
        获取集合统计信息

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            统计信息字典
        """
        collection = self._get_or_create_collection(knowledge_base_id)

        try:
            count = collection.count()
            return {
                "knowledge_base_id": knowledge_base_id,
                "total_chunks": count
            }
        except Exception as e:
            logger.error(f"获取集合统计失败: {e}")
            return {
                "knowledge_base_id": knowledge_base_id,
                "total_chunks": 0
            }


# 全局单例
_chroma_service: ChromaService = None


def get_chroma_service() -> ChromaService:
    """获取 Chroma 服务单例"""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
