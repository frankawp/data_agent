"""
命令基类

定义命令的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import List

from rich.console import Console


class Command(ABC):
    """命令基类"""

    name: str = ""  # 命令名称（如 "plan"）
    aliases: List[str] = []  # 命令别名
    description: str = ""  # 命令描述
    usage: str = ""  # 使用说明

    @abstractmethod
    def execute(self, args: List[str], console: Console) -> bool:
        """
        执行命令

        Args:
            args: 命令参数列表
            console: Rich Console 实例

        Returns:
            是否处理成功
        """
        pass

    def get_help(self) -> str:
        """获取帮助信息"""
        usage_str = f" {self.usage}" if self.usage else ""
        return f"/{self.name}{usage_str} - {self.description}"
