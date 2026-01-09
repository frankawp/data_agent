"""配置管理"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # Anthropic API配置
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # 模型配置
    model_name: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.7

    # 数据库配置
    db_connection: Optional[str] = None

    # 执行配置
    max_execution_time: int = 300  # 最大执行时间（秒）
    enable_parallel_execution: bool = True  # 是否启用并行执行

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()
