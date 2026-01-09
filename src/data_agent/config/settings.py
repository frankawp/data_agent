"""
配置管理模块

从环境变量或.env文件加载配置，管理数据库连接、API密钥等。
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 智谱AI配置
    zhipu_api_key: str = Field(
        default="",
        alias="API_KEY",
        description="智谱AI API密钥"
    )
    zhipu_base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4/",
        alias="BASE_URL",
        description="智谱AI API基础URL"
    )
    zhipu_model: str = Field(
        default="glm-4.7",
        alias="MODEL",
        description="智谱AI模型名称"
    )

    # 数据库配置
    db_connection: str = Field(
        default="",
        alias="DB_CONNECTION",
        description="数据库连接字符串"
    )

    # MicroSandbox配置
    sandbox_enabled: bool = Field(
        default=True,
        description="是否启用MicroSandbox沙箱"
    )
    sandbox_server_url: str = Field(
        default="http://localhost:8080",
        description="MicroSandbox服务器地址"
    )
    sandbox_timeout: int = Field(
        default=30,
        description="沙箱执行超时时间（秒）"
    )
    sandbox_memory: int = Field(
        default=2048,
        description="沙箱内存限制（MB）"
    )

    # DuckDB配置
    duckdb_memory_limit: str = Field(
        default="4GB",
        description="DuckDB内存限制"
    )
    duckdb_threads: int = Field(
        default=4,
        description="DuckDB线程数"
    )

    # Agent配置
    max_iterations: int = Field(
        default=10,
        description="Agent最大迭代次数"
    )
    conversation_memory_size: int = Field(
        default=20,
        description="对话历史记录数量"
    )

    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="日志文件路径"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def validate_config(self) -> list[str]:
        """验证配置，返回错误列表"""
        errors = []

        if not self.zhipu_api_key:
            errors.append("缺少智谱AI API密钥 (API_KEY)")

        if not self.db_connection:
            errors.append("缺少数据库连接字符串 (DB_CONNECTION)")

        return errors

    def get_db_type(self) -> str:
        """获取数据库类型"""
        if not self.db_connection:
            return "unknown"
        if "mysql" in self.db_connection.lower():
            return "mysql"
        elif "postgresql" in self.db_connection.lower() or "postgres" in self.db_connection.lower():
            return "postgresql"
        elif "sqlite" in self.db_connection.lower():
            return "sqlite"
        return "unknown"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


def reload_settings() -> Settings:
    """重新加载配置"""
    get_settings.cache_clear()
    return get_settings()
