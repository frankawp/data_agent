"""
模式管理模块

定义所有运行时模式及其管理逻辑，支持配置持久化。
"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from pydantic import BaseModel, Field


class PlanModeValue(str, Enum):
    """Plan Mode 的三个状态"""
    OFF = "off"
    ON = "on"
    AUTO = "auto"


class PreviewLimitValue(str, Enum):
    """Preview Limit 的可选值"""
    LIMIT_10 = "10"
    LIMIT_50 = "50"
    LIMIT_100 = "100"
    ALL = "all"

    def to_int(self) -> Optional[int]:
        """转换为整数，all 返回 None"""
        if self == PreviewLimitValue.ALL:
            return None
        return int(self.value)


class ModeConfig(BaseModel):
    """运行时模式配置"""

    # 核心模式
    plan_mode: PlanModeValue = Field(
        default=PlanModeValue.OFF,
        description="计划模式：off=直接执行, on=先规划后确认, auto=复杂任务自动规划"
    )
    auto_execute: bool = Field(
        default=True,
        description="自动执行：是否自动执行工具调用"
    )
    safe_mode: bool = Field(
        default=True,
        description="安全模式：严格限制危险 SQL 操作"
    )
    verbose: bool = Field(
        default=False,
        description="详细模式：显示详细的思考过程"
    )

    # 数据分析专用模式
    preview_limit: PreviewLimitValue = Field(
        default=PreviewLimitValue.LIMIT_50,
        description="数据预览行数限制"
    )
    export_mode: bool = Field(
        default=False,
        description="自动导出：是否自动保存结果到文件"
    )

    class Config:
        use_enum_values = False


# 模式定义信息
MODE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "plan": {
        "attr": "plan_mode",
        "display_name": "计划模式",
        "description": "控制任务规划行为",
        "allowed_values": ["off", "on", "auto"],
        "env_key": "DATA_AGENT_PLAN_MODE",
    },
    "auto": {
        "attr": "auto_execute",
        "display_name": "自动执行",
        "description": "是否自动执行工具调用",
        "allowed_values": ["on", "off"],
        "env_key": "DATA_AGENT_AUTO_EXECUTE",
    },
    "safe": {
        "attr": "safe_mode",
        "display_name": "安全模式",
        "description": "限制危险 SQL 操作",
        "allowed_values": ["on", "off"],
        "env_key": "DATA_AGENT_SAFE_MODE",
    },
    "verbose": {
        "attr": "verbose",
        "display_name": "详细输出",
        "description": "显示详细思考过程",
        "allowed_values": ["on", "off"],
        "env_key": "DATA_AGENT_VERBOSE",
    },
    "preview": {
        "attr": "preview_limit",
        "display_name": "预览行数",
        "description": "数据预览的最大行数",
        "allowed_values": ["10", "50", "100", "all"],
        "env_key": "DATA_AGENT_PREVIEW_LIMIT",
    },
    "export": {
        "attr": "export_mode",
        "display_name": "自动导出",
        "description": "自动保存结果到文件",
        "allowed_values": ["on", "off"],
        "env_key": "DATA_AGENT_EXPORT_MODE",
    },
}


class ModeManager:
    """
    模式管理器

    负责模式的读取、修改、持久化和状态显示。
    使用单例模式确保全局状态一致。
    """

    _instance: Optional["ModeManager"] = None
    _config_file: Path = Path.home() / ".data_agent" / "modes.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config = ModeConfig()
        self._callbacks: Dict[str, List[Callable]] = {}
        self._load_from_file()
        self._load_from_env()

    def _load_from_file(self) -> None:
        """从 JSON 文件加载配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 转换枚举值
                    if "plan_mode" in data:
                        data["plan_mode"] = PlanModeValue(data["plan_mode"])
                    if "preview_limit" in data:
                        data["preview_limit"] = PreviewLimitValue(data["preview_limit"])
                    self._config = ModeConfig(**data)
            except Exception:
                pass  # 加载失败使用默认值

    def _load_from_env(self) -> None:
        """从环境变量加载配置（优先级高于文件）"""
        for mode_key, definition in MODE_DEFINITIONS.items():
            env_key = definition.get("env_key")
            if env_key and env_key in os.environ:
                value = os.environ[env_key]
                self._set_mode_internal(mode_key, value)

    def _save_to_file(self) -> None:
        """保存配置到 JSON 文件"""
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        for mode_key, definition in MODE_DEFINITIONS.items():
            attr = definition["attr"]
            value = getattr(self._config, attr)
            # 转换枚举为字符串
            if isinstance(value, Enum):
                value = value.value
            data[attr] = value

        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, mode_key: str) -> Any:
        """获取模式值"""
        if mode_key not in MODE_DEFINITIONS:
            raise ValueError(f"未知的模式: {mode_key}")
        attr = MODE_DEFINITIONS[mode_key]["attr"]
        return getattr(self._config, attr)

    def set(self, mode_key: str, value: Any, persist: bool = True) -> bool:
        """
        设置模式值

        Args:
            mode_key: 模式键名（如 "plan", "auto"）
            value: 新值
            persist: 是否持久化到文件

        Returns:
            是否设置成功
        """
        if mode_key not in MODE_DEFINITIONS:
            return False

        old_value = self.get(mode_key)
        success = self._set_mode_internal(mode_key, value)

        if success:
            if persist:
                self._save_to_file()
            # 触发回调
            self._trigger_callbacks(mode_key, old_value, self.get(mode_key))

        return success

    def _set_mode_internal(self, mode_key: str, value: Any) -> bool:
        """内部设置模式值"""
        definition = MODE_DEFINITIONS[mode_key]
        attr = definition["attr"]

        try:
            if attr == "plan_mode":
                if isinstance(value, str):
                    value = PlanModeValue(value.lower())
            elif attr == "preview_limit":
                if isinstance(value, str):
                    value = PreviewLimitValue(value)
            elif isinstance(value, str):
                # 布尔值转换
                value = value.lower() in ("on", "true", "1", "yes")

            setattr(self._config, attr, value)
            return True
        except (ValueError, KeyError):
            return False

    def toggle(self, mode_key: str) -> Any:
        """切换布尔模式"""
        if mode_key not in MODE_DEFINITIONS:
            return None

        attr = MODE_DEFINITIONS[mode_key]["attr"]
        current = getattr(self._config, attr)

        if isinstance(current, bool):
            new_value = not current
            self.set(mode_key, new_value)
            return new_value
        return None

    def register_callback(self, mode_key: str, callback: Callable) -> None:
        """注册模式变更回调"""
        if mode_key not in self._callbacks:
            self._callbacks[mode_key] = []
        self._callbacks[mode_key].append(callback)

    def _trigger_callbacks(self, mode_key: str, old_value: Any, new_value: Any) -> None:
        """触发回调"""
        for callback in self._callbacks.get(mode_key, []):
            try:
                callback(mode_key, old_value, new_value)
            except Exception:
                pass  # 回调失败不影响主流程

    @property
    def config(self) -> ModeConfig:
        """获取完整配置"""
        return self._config

    def display_modes(self, console) -> None:
        """使用 Rich 显示当前模式状态"""
        from rich.table import Table
        from rich.panel import Panel

        table = Table(
            title="当前模式状态",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("命令", style="cyan", width=12)
        table.add_column("当前值", style="green", width=10)
        table.add_column("说明", style="dim")

        for mode_key, definition in MODE_DEFINITIONS.items():
            value = self.get(mode_key)
            # 格式化显示值
            if isinstance(value, bool):
                display_value = "[green]ON[/green]" if value else "[red]OFF[/red]"
            elif isinstance(value, Enum):
                display_value = f"[yellow]{value.value}[/yellow]"
            else:
                display_value = str(value)

            table.add_row(
                f"/{mode_key}",
                display_value,
                definition["description"]
            )

        console.print(Panel(table, border_style="blue"))

    def reset_to_defaults(self) -> None:
        """重置所有模式为默认值"""
        self._config = ModeConfig()
        self._save_to_file()

    def get_all(self) -> Dict[str, Any]:
        """获取所有模式的当前值"""
        result = {}
        for mode_key in MODE_DEFINITIONS:
            result[mode_key] = self.get(mode_key)
        return result


def get_mode_manager() -> ModeManager:
    """获取模式管理器单例"""
    return ModeManager()
