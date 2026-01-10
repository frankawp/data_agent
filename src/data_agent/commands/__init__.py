"""
命令系统模块

提供斜杠命令的注册和执行功能。
"""

from .base import Command
from .registry import CommandRegistry, get_registry
from .mode_commands import register_all_commands

__all__ = [
    "Command",
    "CommandRegistry",
    "get_registry",
    "register_all_commands",
]
