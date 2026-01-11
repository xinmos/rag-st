from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从环境变量或 .env 文件读取"""

    # 数据库配置
    db_url: str = "sqlite+aiosqlite:///./app.db"

    # JWT 配置
    jwt_secret: str = "rag-st-secret-xxq"
    jwt_algorithm: str = "HS256"

    # Redis 配置（可选，如果不需要可以删除）
    redis_url: Optional[str] = None

    # 应用配置
    app_name: str = "RAG-ST API"
    app_version: str = "0.1.0"
    debug: bool = False

    # 文件上传配置
    upload_dir: str = "uploads"  # 文件上传目录

    # 向量数据库配置
    # 支持: chroma, milvus
    vector_db_type: str = "chroma"  # chroma 或 milvus

    # Milvus 配置（当 vector_db_type=milvus 时使用）
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection_name: str = "rag_documents"

    # Chroma 配置（当 vector_db_type=chroma 时使用）
    chroma_persist_directory: str = "./chroma_db"  # Chroma 数据存储目录

    # Embedding 模型配置
    # 支持的后端: sentence_transformer, ollama
    embedding_backend: str = "ollama"
    # 模型名称:
    # - Sentence Transformer: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" (384维)
    # - Ollama: "nomic-embed-text" (768维)
    embedding_model: str = "ollama/nomic-embed-text"
    embedding_dimension: int = 768  # nomic-embed-text 是 768 维
    embedding_device: str = "cpu"  # cpu 或 cuda

    # Ollama 配置
    ollama_base_url: str = "http://192.168.1.6:11434"

    # LLM 配置
    # 支持的后端类型: auto, ollama, openai, mock
    llm_backend: str = "ollama"
    llm_model: str = "qwen2.5:7b"  # Ollama 模型名称

    # LLM API 配置（用于 OpenAI 兼容 API）
    # Ollama: http://192.168.1.6:11434
    # 其他 OpenAI 兼容 API: 设置相应的 URL
    llm_api_base: str = "http://192.168.1.6:11434"
    llm_api_key: Optional[str] = None

    # 日志配置
    log_file: Optional[str] = "logs/app.log"  # 日志文件路径，None 表示不输出到文件
    log_level: str = "INFO"  # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_to_file: bool = True  # 是否输出到文件
    log_to_console: bool = True  # 是否输出到控制台
    log_max_bytes: int = 10 * 1024 * 1024  # 单个日志文件最大字节数 (10MB)
    log_backup_count: int = 5  # 保留的备份文件数量

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# 全局配置实例
settings = Settings()
