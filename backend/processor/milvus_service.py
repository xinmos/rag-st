"""
Milvus 向量数据库服务
"""
from typing import List, Dict, Tuple, Optional
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)

from common.config import settings
from common.logger import get_logger

logger = get_logger(__name__)


class MilvusService:
    """Milvus 向量数据库服务"""

    def __init__(self):
        self._connected = False
        self._collection = None

    def connect(self):
        """连接到 Milvus"""
        if self._connected:
            return

        try:
            connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=settings.milvus_port
            )
            self._connected = True
            logger.info(f"成功连接到 Milvus: {settings.milvus_host}:{settings.milvus_port}")
        except Exception as e:
            logger.error(f"连接 Milvus 失败: {e}")
            raise

    def create_collection(self):
        """创建集合"""
        if self._collection is not None:
            return

        self.connect()

        collection_name = settings.milvus_collection_name

        # 检查集合是否存在
        if utility.has_collection(collection_name):
            self._collection = Collection(collection_name)
            logger.info(f"集合已存在: {collection_name}")
            return

        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="knowledge_base_id", dtype=DataType.INT64),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_id", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.embedding_dimension),
        ]

        # 创建 schema
        schema = CollectionSchema(
            fields=fields,
            description="RAG 文档向量集合",
            enable_dynamic_field=True
        )

        # 创建集合
        self._collection = Collection(
            name=collection_name,
            schema=schema
        )

        # 创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        self._collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

        logger.info(f"成功创建集合: {collection_name}")

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
        if self._collection is None:
            self.create_collection()

        data = [
            {
                "knowledge_base_id": knowledge_base_id,
                "document_id": document_id,
                "chunk_id": chunk_id,
                "text": text,
                "embedding": embedding,
            }
            for chunk_id, text, embedding in chunks
        ]

        try:
            insert_result = self._collection.insert(data)
            self._collection.flush()
            logger.info(f"成功插入 {len(data)} 个文档块")
            return insert_result
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
        if self._collection is None:
            self.create_collection()

        # 加载集合
        self._collection.load()

        # 构建搜索表达式
        expr = f"knowledge_base_id == {knowledge_base_id}"

        # 搜索参数
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }

        try:
            results = self._collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["text", "document_id", "chunk_id"]
            )

            # 格式化结果
            formatted_results = []
            for hit in results[0]:
                formatted_results.append({
                    "text": hit.entity.get("text"),
                    "document_id": hit.entity.get("document_id"),
                    "chunk_id": hit.entity.get("chunk_id"),
                    "score": float(hit.score),
                })

            return formatted_results

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise

    def delete_document(self, document_id: int):
        """
        删除文档的所有向量

        Args:
            document_id: 文档ID
        """
        if self._collection is None:
            self.create_collection()

        try:
            expr = f"document_id == {document_id}"
            self._collection.delete(expr)
            logger.info(f"成功删除文档 {document_id} 的向量")
        except Exception as e:
            logger.error(f"删除文档向量失败: {e}")
            raise


# 全局单例
_milvus_service: MilvusService = None


def get_milvus_service() -> MilvusService:
    """获取 Milvus 服务单例"""
    global _milvus_service
    if _milvus_service is None:
        _milvus_service = MilvusService()
    return _milvus_service
