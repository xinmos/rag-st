"""
RAG 服务 - 检索增强生成
"""
from typing import List, Dict, AsyncGenerator
from fastapi import HTTPException, status

from common.context import get_request_context
from common.entity.schemas.document import ChatResponse
from common.logger import get_logger

logger = get_logger(__name__)


class RagService:
    """RAG 服务"""

    @staticmethod
    async def chat(knowledge_base_id: int, message: str) -> ChatResponse:
        """
        基于知识库的问答

        Args:
            knowledge_base_id: 知识库ID
            message: 用户消息

        Returns:
            ChatResponse: 问答响应
        """
        from models.knowledge_base import KnowledgeBase
        from processor import get_embedding_service, get_vector_db_service, get_llm_service

        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        # 验证知识库是否存在
        kb = await KnowledgeBase.get_by_id(knowledge_base_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        # 1. 向量化用户问题
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.encode(message)
        query_vector = query_embedding.tolist()

        # 2. 检索相关文档
        vector_db_service = get_vector_db_service()
        search_results = vector_db_service.search(
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_vector,
            top_k=3
        )

        if not search_results:
            return ChatResponse(
                answer="抱歉，我在知识库中没有找到相关信息。",
                sources=[]
            )

        # 3. 构建 prompt
        context_text = "\n\n".join([
            f"[文档片段 {i+1}]\n{result['text']}"
            for i, result in enumerate(search_results)
        ])

        prompt = f"""基于以下文档内容回答用户问题。如果文档中没有相关信息，请明确说明。

文档内容:
{context_text}

用户问题: {message}

请基于上述文档内容给出准确、详细的回答。"""

        # 4. 调用 LLM 生成回答
        try:
            llm_service = get_llm_service()
            system_prompt = "你是一个专业的问答助手，基于提供的文档内容回答用户问题。"
            answer = await llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1000
            )
        except Exception as e:
            logger.error(f"LLM 生成回答失败: {e}")
            # 如果 LLM 失败，返回检索到的文档内容
            answer = f"根据检索到的文档内容：\n\n{context_text}"

        # 5. 构建来源信息
        sources = [
            {
                "document_id": result["document_id"],
                "chunk_id": result["chunk_id"],
                "score": result["score"]
            }
            for result in search_results
        ]

        return ChatResponse(answer=answer, sources=sources)

    @staticmethod
    async def chat_stream(knowledge_base_id: int, message: str) -> AsyncGenerator[str, None]:
        """
        基于知识库的流式问答

        Args:
            knowledge_base_id: 知识库ID
            message: 用户消息

        Yields:
            str: 生成的文本片段
        """
        from models.knowledge_base import KnowledgeBase
        from processor import get_embedding_service, get_vector_db_service, get_llm_service

        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        # 验证知识库是否存在
        kb = await KnowledgeBase.get_by_id(knowledge_base_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        # 1. 向量化用户问题
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.encode(message)
        query_vector = query_embedding.tolist()

        # 2. 检索相关文档
        vector_db_service = get_vector_db_service()
        search_results = vector_db_service.search(
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_vector,
            top_k=3
        )

        # 3. 构建 prompt
        context_text = "\n\n".join([
            f"[文档片段 {i+1}]\n{result['text']}"
            for i, result in enumerate(search_results)
        ])

        prompt = f"""基于以下文档内容回答用户问题。如果文档中没有相关信息，请明确说明。

文档内容:
{context_text}

用户问题: {message}

请基于上述文档内容给出准确、详细的回答。"""

        # 4. 调用 LLM 流式生成回答
        try:
            llm_service = get_llm_service()
            system_prompt = "你是一个专业的问答助手，基于提供的文档内容回答用户问题。"
            async for chunk in llm_service.stream_generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1000
            ):
                yield chunk
        except Exception as e:
            logger.error(f"LLM 流式生成失败: {e}")
            # 如果 LLM 失败，返回检索到的文档内容
            answer = f"根据检索到的文档内容：\n\n{context_text}"
            # 模拟流式输出
            for char in answer:
                yield char

    @staticmethod
    async def get_context_sources(knowledge_base_id: int, message: str) -> List[Dict]:
        """
        获取检索到的相关文档来源

        Args:
            knowledge_base_id: 知识库ID
            message: 用户消息

        Returns:
            List[Dict]: 相关文档来源列表
        """
        from models.knowledge_base import KnowledgeBase
        from processor import get_embedding_service, get_vector_db_service

        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        # 验证知识库是否存在
        kb = await KnowledgeBase.get_by_id(knowledge_base_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        # 向量化用户问题
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.encode(message)
        query_vector = query_embedding.tolist()

        # 检索相关文档
        vector_db_service = get_vector_db_service()
        search_results = vector_db_service.search(
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_vector,
            top_k=5
        )

        # 构建来源信息
        sources = [
            {
                "document_id": result["document_id"],
                "chunk_id": result["chunk_id"],
                "text": result["text"],
                "score": result["score"]
            }
            for result in search_results
        ]

        return sources
