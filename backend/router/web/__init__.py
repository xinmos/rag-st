from .chat import router as chat_router
from .document import router as document_router
from .knowledge_base import router as knowledge_base_router
from .user import router as user_router

__all__ = ["user_router", "knowledge_base_router", "document_router", "chat_router"]
