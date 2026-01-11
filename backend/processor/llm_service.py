"""
LLM 服务 - 支持多种大语言模型后端
支持 Ollama、OpenAI 兼容 API 等
"""
import asyncio
from typing import List, Dict, Optional, AsyncGenerator, Union
from abc import ABC, abstractmethod

from common.config import settings
from common.logger import get_logger

logger = get_logger(__name__)


class LLMBackend(ABC):
    """LLM 后端抽象基类"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        生成回答

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            生成的回答
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        """
        流式生成回答

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            生成的文本片段
        """
        pass


class OllamaBackend(LLMBackend):
    """Ollama 后端（本地模型）"""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.llm_api_base or settings.ollama_base_url).rstrip('/')
        self.model = model or settings.llm_model
        logger.info(f"初始化 Ollama 后端: {self.base_url}, 模型: {self.model}")

    async def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False):
        """调用 Ollama API"""
        import httpx

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "num_predict": 1000
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            return response

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """生成回答"""
        try:
            response = await self._call_ollama(prompt, system_prompt, stream=False)
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama 生成失败: {e}")
            raise

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        """流式生成回答"""
        try:
            response = await self._call_ollama(prompt, system_prompt, stream=True)

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    import json
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Ollama 流式生成失败: {e}")
            raise


class OpenAIBackend(LLMBackend):
    """OpenAI 兼容 API 后端"""

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None
    ):
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.model = model or settings.llm_model
        self.default_headers = default_headers or {}
        logger.info(f"初始化 OpenAI 后端: {self.api_base}, 模型: {self.model}")

    async def _call_openai(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False):
        """调用 OpenAI API"""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        headers.update(self.default_headers)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": 0.7,
            "max_tokens": 1000
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """生成回答"""
        try:
            response = await self._call_openai(prompt, system_prompt, stream=False)
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI 生成失败: {e}")
            raise

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        """流式生成回答"""
        try:
            response = await self._call_openai(prompt, system_prompt, stream=True)

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    import json
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"OpenAI 流式生成失败: {e}")
            raise


class MockBackend(LLMBackend):
    """Mock 后端，用于测试"""

    def __init__(self):
        logger.info("初始化 Mock 后端")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """生成模拟回答"""
        await asyncio.sleep(0.5)
        return "[Mock 回答] 这是一个模拟的回答。实际使用时请配置真实的 LLM 后端。"

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        """流式生成模拟回答"""
        mock_text = "[Mock 回答] 这是一个模拟的回答。实际使用时请配置真实的 LLM 后端。"
        for char in mock_text:
            await asyncio.sleep(0.05)
            yield char


class LLMService:
    """LLM 服务，统一接口"""

    def __init__(self, backend: Optional[LLMBackend] = None):
        self.backend = backend

    def _ensure_backend(self):
        """确保后端已初始化"""
        if self.backend is None:
            raise ValueError("LLM 后端未配置。请在配置中设置 llm_api_base 或 llm_backend")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """生成回答"""
        self._ensure_backend()
        return await self.backend.generate(prompt, system_prompt, temperature, max_tokens)

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        """流式生成回答"""
        self._ensure_backend()
        async for chunk in self.backend.stream_generate(prompt, system_prompt, temperature, max_tokens):
            yield chunk


def create_llm_backend(
    backend_type: str = "auto",
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> LLMBackend:
    """
    创建 LLM 后端

    Args:
        backend_type: 后端类型 (auto, ollama, openai, mock)
        api_base: API 基础 URL
        api_key: API 密钥
        model: 模型名称

    Returns:
        LLM 后端实例
    """
    if backend_type == "mock":
        return MockBackend()

    if backend_type == "auto":
        # 自动检测：如果有 api_base，尝试解析
        api_base = api_base or settings.llm_api_base
        if api_base:
            if "11434" in api_base or "ollama" in api_base.lower():
                backend_type = "ollama"
            else:
                backend_type = "openai"
        else:
            # 默认使用 Ollama，从配置读取地址
            backend_type = "ollama"
            api_base = settings.llm_api_base or settings.ollama_base_url

    if backend_type == "ollama":
        return OllamaBackend(
            base_url=api_base or settings.llm_api_base or settings.ollama_base_url,
            model=model or settings.llm_model
        )

    elif backend_type == "openai":
        if not api_key:
            raise ValueError("OpenAI 后端需要 api_key")
        return OpenAIBackend(
            api_base=api_base or settings.llm_api_base,
            api_key=api_key,
            model=model or settings.llm_model
        )

    else:
        raise ValueError(f"不支持的 LLM 后端类型: {backend_type}")


# 全局单例
_llm_service: LLMService = None


def get_llm_service() -> LLMService:
    """获取 LLM 服务单例"""
    global _llm_service
    if _llm_service is None:
        # 创建后端
        backend = create_llm_backend()
        _llm_service = LLMService(backend=backend)
    return _llm_service
