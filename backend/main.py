from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
import uvloop
import socketio
from common.entity.base_response import BaseResponse
from common.logger import get_logger, init_logging
from common.middlewares.log_middleware import LoggingMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router.web import *
from router.sio import register_socketio_handlers

# 初始化日志系统
init_logging()
logger = get_logger(__name__)

# 使用 uvloop 作为事件循环
uvloop.install()

# 创建 Socket.IO 服务器
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,  # 临时启用日志查看连接问题
    engineio_logger=False,
    socketio_path='/socket.io'  # 明确指定路径
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 注册 Socket.IO 处理器
    register_socketio_handlers(sio)
    yield


app = FastAPI(
    title="RAG-ST API",
    description="RAG-ST API Documentation",
    version="0.1.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)

# Health 接口直接定义在 main.py
@app.get("/health", response_model=BaseResponse[Optional[str]], tags=["health"])
async def health_check():
    """健康检查接口"""
    return BaseResponse(code=0, message="success", data="ok")

# 注册路由
app.include_router(user_router)
app.include_router(knowledge_base_router)
app.include_router(document_router)
app.include_router(chat_router)

# 将 Socket.IO 附加到 FastAPI 应用
socketio_app = socketio.ASGIApp(sio, app)


if __name__ == "__main__":
    uvicorn.run(
        "main:socketio_app",
        host="0.0.0.0",
        port=8000,
        loop="uvloop",
        reload=True
    )
