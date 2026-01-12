"""
CopilotKit Web API 模块

提供 FastAPI 后端，集成 CopilotKit SDK，连接现有 DataAgent。
"""

from .main import app, main

__all__ = ["app", "main"]
