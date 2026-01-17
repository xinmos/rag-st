"""
Socket.IO 聊天路由
"""
from typing import Dict

from socketio import AsyncServer

from common import RequestContext
from common.context import set_request_context
from common.logger import get_logger
from common.orm.db import get_db_session
from common.utils import decode_access_token
from services import RagService

logger = get_logger(__name__)


class SocketIOChatHandler:
    """Socket.IO 聊天处理器"""

    def __init__(self, sio: AsyncServer):
        self.sio = sio
        self._setup_handlers()

    def _setup_handlers(self):
        """设置 Socket.IO 事件处理器"""

        @self.sio.event
        async def connect(sid, environ, auth):
            """客户端连接"""
            # 验证 JWT token
            token = auth.get('token') if auth else None
            if not token:
                return False

            try:
                payload = decode_access_token(token)
                user_id = payload.get('sub')

                if not user_id:
                    return False

                # 保存用户会话信息
                await self.sio.save_session(sid, {'user_id': user_id})
                logger.info(f"用户 {user_id} 连接成功, sid: {sid}")
                return True

            except Exception as e:
                logger.error(f"连接验证失败: {e}")
                return False

        @self.sio.event
        async def disconnect(sid):
            """客户端断开连接"""
            try:
                session = await self.sio.get_session(sid)
                user_id = session.get('user_id') if session else None
                logger.info(f"用户 {user_id} 断开连接, sid: {sid}")
            except Exception:
                pass

        @self.sio.event
        async def chat_message(sid, data: Dict):
            """
            处理聊天消息

            Args:
                sid: 会话ID
                data: 消息数据 {knowledge_base_id, message}
            """
            try:
                session = await self.sio.get_session(sid)
                if not session:
                    await self.sio.emit('error', {'message': '未登录'}, to=sid)
                    return

                user_id = session.get('user_id')
                knowledge_base_id = data.get('knowledge_base_id')
                message = data.get('message', '')

                if not knowledge_base_id or not message:
                    await self.sio.emit('error', {'message': '参数错误'}, to=sid)
                    return

                logger.info(f"用户 {user_id} 发送消息: {message[:50]}...")

                # 发送开始响应
                await self.sio.emit('chat_start', {
                    'knowledge_base_id': knowledge_base_id,
                    'message': message
                }, to=sid)

                # 流式生成回答
                logger.info(f"开始流式生成回答: sid={sid}, kb_id={knowledge_base_id}")
                await self._stream_answer(sid, knowledge_base_id, message, user_id)
                logger.info(f"流式生成完成: sid={sid}")

            except Exception as e:
                logger.error(f"处理消息失败: {e}", exc_info=True)
                await self.sio.emit('error', {'message': str(e)}, to=sid)

    async def _stream_answer(self, sid: int, knowledge_base_id: int, message: str, user_id: int):
        """
        流式生成并发送回答（限速：每 0.2 秒发送一次）

        Args:
            sid: 会话ID
            knowledge_base_id: 知识库ID
            message: 用户消息
            user_id: 用户ID
        """
        import asyncio

        try:
            async with get_db_session() as session:
                ctx = RequestContext(
                    session=session,
                    user_id=int(user_id),
                    path="/chat/stream",
                    method="SOCKETIO"
                )
                set_request_context(ctx)

                # 限速配置
                chunk_interval = 0.2  # 每 0.2 秒发送一次
                # 使用 RAG 服务的流式生成
                full_answer = ""
                buffer = ""
                send_count = 0
                last_send_time = asyncio.get_event_loop().time()

                async for chunk in RagService.chat_stream(knowledge_base_id, message):
                    full_answer += chunk
                    buffer += chunk

                    current_time = asyncio.get_event_loop().time()
                    elapsed = current_time - last_send_time

                    # 如果距离上次发送超过 0.2 秒，或者累积了足够内容，则发送
                    if elapsed >= chunk_interval and buffer:
                        send_count += 1
                        logger.debug(f"发送第 {send_count} 批: {len(buffer)} 字符")
                        await self.sio.emit('chat_chunk', {
                            'content': buffer,
                            'is_complete': False
                        }, to=sid)
                        buffer = ""
                        last_send_time = current_time

                # 发送剩余内容
                if buffer:
                    send_count += 1
                    logger.debug(f"发送最后一批: {len(buffer)} 字符")
                    await self.sio.emit('chat_chunk', {
                        'content': buffer,
                        'is_complete': False
                    }, to=sid)

                logger.info(f"流式发送完成: 共 {send_count} 批, 总长度: {len(full_answer)}")

                # 获取来源信息
                sources = await RagService.get_context_sources(knowledge_base_id, message)

                # 发送完成信号
                await self.sio.emit('chat_complete', {
                    'answer': full_answer,
                    'sources': sources
                }, to=sid)

        except Exception as e:
            logger.error(f"流式生成失败: {e}", exc_info=True)
            await self.sio.emit('error', {'message': str(e)}, to=sid)


def register_socketio_handlers(sio: AsyncServer):
    """注册 Socket.IO 处理器"""
    SocketIOChatHandler(sio)
