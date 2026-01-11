"""
向量数据库抽象服务
根据配置自动选择 Chroma 或 Milvus
"""
from typing import List, Dict, Tuple

from common.config import settings
from common.logger import get_logger

logger = get_logger(__name__)


class VectorDBService:
    """向量数据库抽象服务"""

    def __init__(self):
        self._service = None
        self._service_type = None

    def _get_service(self):
        """获取实际的向量数据库服务"""
        if self._service is not None:
            return self._service

        vector_db_type = settings.vector_db_type.lower()

        if vector_db_type == "chroma":
            from .chroma_service import ChromaService
            self._service = ChromaService()
            self._service_type = "chroma"
            logger.info("使用 Chroma 向量数据库")
        elif vector_db_type == "milvus":
            from .milvus_service import MilvusService
            self._service = MilvusService()
            self._service_type = "milvus"
            logger.info("使用 Milvus 向量数据库")
        else:
            raise ValueError(f"不支持的向量数据库类型: {vector_db_type}")

        return self._service

    def insert_chunks(
        self,
        knowledge_base_id: int,
        document_id: int,
        chunks: List[Tuple[int, str, list]]
    ):
        """插入文档块"""
        service = self._get_service()
        return service.insert_chunks(knowledge_base_id, document_id, chunks)

    def search(
        self,
        knowledge_base_id: int,
        query_embedding: list,
        top_k: int = 5
    ) -> List[Dict]:
        """向量搜索"""
        service = self._get_service()
        return service.search(knowledge_base_id, query_embedding, top_k)

    def delete_document(self, knowledge_base_id: int, document_id: int):
        """删除文档的所有向量"""
        service = self._get_service()
        return service.delete_document(knowledge_base_id, document_id)

    def delete_knowledge_base(self, knowledge_base_id: int):
        """删除整个知识库的向量"""
        service = self._get_service()
        if hasattr(service, 'delete_knowledge_base'):
            return service.delete_knowledge_base(knowledge_base_id)

    def get_collection_stats(self, knowledge_base_id: int) -> Dict:
        """获取集合统计信息"""
        service = self._get_service()
        if hasattr(service, 'get_collection_stats'):
            return service.get_collection_stats(knowledge_base_id)
        return {"knowledge_base_id": knowledge_base_id, "total_chunks": 0}


# 全局单例
_vector_db_service: VectorDBService = None


def get_vector_db_service() -> VectorDBService:
    """获取向量数据库服务单例"""
    global _vector_db_service
    if _vector_db_service is None:
        _vector_db_service = VectorDBService()
    return _vector_db_service
