import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import orjson

from .config import settings


class JSONFormatter(logging.Formatter):
    """JSON 格式的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 如果有异常信息，添加到日志中
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # orjson.dumps() 返回 bytes，需要解码为 str
        return orjson.dumps(log_data, option=orjson.OPT_NON_STR_KEYS).decode('utf-8')


def setup_logging(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    初始化日志配置
    
    Args:
        log_file: 日志文件路径，如果为 None 则使用配置中的路径
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否输出到文件
        log_to_console: 是否输出到控制台
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的备份文件数量
    """
    # 获取日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 清除现有的处理器
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    
    # 控制台处理器（使用标准格式）
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # 文件处理器（使用 JSON 格式）
    if log_to_file:
        if log_file is None:
            log_file = getattr(settings, 'log_file', 'logs/app.log')
        
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用 RotatingFileHandler 支持日志轮转
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    
    return root_logger


# 从配置中初始化日志
def init_logging():
    """从配置中初始化日志系统"""
    log_file = getattr(settings, 'log_file', None)
    log_level = getattr(settings, 'log_level', 'INFO')
    log_to_file = getattr(settings, 'log_to_file', True)
    log_to_console = getattr(settings, 'log_to_console', True)
    log_max_bytes = getattr(settings, 'log_max_bytes', 10 * 1024 * 1024)
    log_backup_count = getattr(settings, 'log_backup_count', 5)
    
    return setup_logging(
        log_file=log_file,
        log_level=log_level,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        max_bytes=log_max_bytes,
        backup_count=log_backup_count
    )


# 获取 logger 的便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger"""
    return logging.getLogger(name)
