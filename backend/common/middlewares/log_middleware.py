import orjson
from common.logger import get_logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """中间件：监听 HTTP 请求，打印 POST JSON 请求的请求体"""
    
    async def dispatch(self, request: Request, call_next):
        # 如果是 POST 请求且 Content-Type 是 application/json
        if request.method == "POST" and request.headers.get("content-type", "").startswith("application/json"):
            try:
                # 读取请求体
                body = await request.body()
                if body:
                    # 解析 JSON (orjson.loads 可以直接接受 bytes)
                    json_body = orjson.loads(body)
                    # orjson.dumps 返回 bytes，需要解码
                    json_str = orjson.dumps(json_body).decode('utf-8')
                    logger.info(json_str)
                    
                    # 重新创建请求流，因为 body 已经被读取
                    async def receive() -> Message:
                        return {"type": "http.request", "body": body}
                    
                    request._receive = receive
            except orjson.JSONDecodeError:
                logger.warning(f"Failed to parse JSON body for POST request: {request.url.path}")
            except Exception as e:
                logger.error(f"Error in logging middleware: {e}")
        
        response = await call_next(request)
        return response
