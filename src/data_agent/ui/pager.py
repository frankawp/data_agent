"""
步骤历史管理

提供步骤信息存储和查询功能。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class StepInfo:
    """步骤信息"""
    step_num: int
    tool_name: str
    tool_args: dict
    result: str
    timestamp: datetime


class StepPager:
    """
    步骤历史管理器

    存储和管理执行步骤的历史记录。
    """

    def __init__(self, console=None):
        """
        初始化步骤管理器

        Args:
            console: Rich Console 实例（保留用于向后兼容）
        """
        self.console = console
        self.step_history: Dict[int, StepInfo] = {}

    def add_step(self, step_num: int, tool_name: str, tool_args: dict, result: str):
        """添加步骤到历史记录"""
        self.step_history[step_num] = StepInfo(
            step_num=step_num,
            tool_name=tool_name,
            tool_args=tool_args,
            result=result,
            timestamp=datetime.now()
        )

    def get_step(self, step_num: int) -> Optional[StepInfo]:
        """获取步骤信息"""
        return self.step_history.get(step_num)

    def clear_history(self):
        """清空历史记录"""
        self.step_history.clear()

    def get_latest_step_num(self) -> int:
        """获取最新步骤编号"""
        if not self.step_history:
            return 0
        return max(self.step_history.keys())
