"""
工具注册表

管理所有可用工具的注册、查询和获取。
支持：
1. 内置工具自动注册
2. 外部工具动态注册
3. 工具别名
4. 按名称/组获取工具
5. 配置化启用/禁用工具组
"""

import importlib
import logging
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表

    单例模式，管理所有可用的工具函数。

    使用示例:
        registry = get_tool_registry()

        # 按名称获取工具
        tool = registry.get("execute_sql")

        # 批量获取
        tools = registry.get_many(["list_tables", "describe_table"])

        # 获取工具组
        sql_tools = registry.get_group("sql_tools")

        # 注册自定义工具
        registry.register("my_tool", my_tool_func)

        # 注册别名
        registry.register_alias("db_query", "execute_sql")
    """

    # 内置工具组定义
    BUILTIN_GROUPS: Dict[str, Dict[str, Any]] = {
        "sql_tools": {
            "module": "data_agent.tools.sql_tools",
            "tools": ["execute_sql", "list_tables", "describe_table"],
        },
        "python_tools": {
            "module": "data_agent.tools.python_tools",
            "tools": [
                "execute_python_safe",
                "list_variables",
                "clear_variables",
                "export_dataframe",
                "export_text",
                "list_exports",
            ],
        },
        "ml_tools": {
            "module": "data_agent.tools.ml_tools",
            "tools": ["train_model", "predict", "list_models"],
        },
    }

    _instance: Optional["ToolRegistry"] = None

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._tools: Dict[str, Callable] = {}
        self._aliases: Dict[str, str] = {}
        self._enabled_groups: Set[str] = set()
        self._disabled_tools: Set[str] = set()
        self._initialized = True

        # 默认注册所有内置工具
        self._register_all_builtin_tools()

    def _register_all_builtin_tools(self):
        """注册所有内置工具"""
        for group_name in self.BUILTIN_GROUPS:
            self._register_builtin_group(group_name)

    def _register_builtin_group(self, group_name: str) -> bool:
        """
        注册内置工具组

        Args:
            group_name: 工具组名称

        Returns:
            是否成功注册
        """
        if group_name not in self.BUILTIN_GROUPS:
            logger.warning(f"未知的工具组: {group_name}")
            return False

        group_info = self.BUILTIN_GROUPS[group_name]
        try:
            module = importlib.import_module(group_info["module"])
            for tool_name in group_info["tools"]:
                tool_func = getattr(module, tool_name, None)
                if tool_func:
                    self._tools[tool_name] = tool_func
                else:
                    logger.warning(f"工具 {tool_name} 在模块 {group_info['module']} 中不存在")

            self._enabled_groups.add(group_name)
            logger.debug(f"已注册工具组: {group_name}")
            return True

        except ImportError as e:
            logger.warning(f"无法加载工具组 {group_name}: {e}")
            return False

    def register(self, name: str, tool: Callable) -> None:
        """
        注册工具

        Args:
            name: 工具名称
            tool: 工具函数（应使用 @tool 装饰器）
        """
        self._tools[name] = tool
        logger.debug(f"已注册工具: {name}")

    def unregister(self, name: str) -> bool:
        """
        取消注册工具

        Args:
            name: 工具名称

        Returns:
            是否成功取消
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug(f"已取消注册工具: {name}")
            return True
        return False

    def register_alias(self, alias: str, target: str) -> None:
        """
        注册工具别名

        Args:
            alias: 别名
            target: 目标工具名称
        """
        self._aliases[alias] = target
        logger.debug(f"已注册工具别名: {alias} -> {target}")

    def get(self, name: str) -> Optional[Callable]:
        """
        获取工具

        Args:
            name: 工具名称或别名

        Returns:
            工具函数，不存在则返回 None
        """
        # 检查是否被禁用
        resolved_name = self._aliases.get(name, name)
        if resolved_name in self._disabled_tools:
            logger.debug(f"工具 {resolved_name} 已被禁用")
            return None

        return self._tools.get(resolved_name)

    def get_many(self, names: List[str]) -> List[Callable]:
        """
        批量获取工具

        Args:
            names: 工具名称列表

        Returns:
            工具函数列表（跳过不存在或禁用的）
        """
        tools = []
        for name in names:
            tool = self.get(name)
            if tool:
                tools.append(tool)
            else:
                logger.warning(f"工具不存在或已禁用: {name}")
        return tools

    def get_group(self, group_name: str) -> List[Callable]:
        """
        获取工具组的所有工具

        Args:
            group_name: 工具组名称

        Returns:
            工具函数列表
        """
        if group_name not in self.BUILTIN_GROUPS:
            logger.warning(f"未知的工具组: {group_name}")
            return []

        return self.get_many(self.BUILTIN_GROUPS[group_name]["tools"])

    def disable_tool(self, name: str) -> None:
        """禁用工具"""
        resolved_name = self._aliases.get(name, name)
        self._disabled_tools.add(resolved_name)
        logger.debug(f"已禁用工具: {resolved_name}")

    def enable_tool(self, name: str) -> None:
        """启用工具"""
        resolved_name = self._aliases.get(name, name)
        self._disabled_tools.discard(resolved_name)
        logger.debug(f"已启用工具: {resolved_name}")

    def disable_group(self, group_name: str) -> None:
        """禁用工具组"""
        if group_name in self.BUILTIN_GROUPS:
            for tool_name in self.BUILTIN_GROUPS[group_name]["tools"]:
                self.disable_tool(tool_name)
            self._enabled_groups.discard(group_name)
            logger.debug(f"已禁用工具组: {group_name}")

    def enable_group(self, group_name: str) -> None:
        """启用工具组"""
        if group_name in self.BUILTIN_GROUPS:
            for tool_name in self.BUILTIN_GROUPS[group_name]["tools"]:
                self.enable_tool(tool_name)
            self._enabled_groups.add(group_name)
            logger.debug(f"已启用工具组: {group_name}")

    def list_tools(self) -> List[str]:
        """列出所有已注册的工具名称"""
        return list(self._tools.keys())

    def list_enabled_tools(self) -> List[str]:
        """列出所有启用的工具名称"""
        return [name for name in self._tools.keys() if name not in self._disabled_tools]

    def list_groups(self) -> List[str]:
        """列出所有工具组名称"""
        return list(self.BUILTIN_GROUPS.keys())

    def list_enabled_groups(self) -> List[str]:
        """列出所有启用的工具组"""
        return list(self._enabled_groups)

    def is_tool_enabled(self, name: str) -> bool:
        """检查工具是否启用"""
        resolved_name = self._aliases.get(name, name)
        return resolved_name in self._tools and resolved_name not in self._disabled_tools

    def apply_config(self, config) -> None:
        """
        应用工具配置

        根据配置启用/禁用工具组，注册别名，加载外部工具。

        Args:
            config: ToolsConfig 对象
        """
        # 应用内置工具组开关
        builtin = config.builtin
        for group_name in self.BUILTIN_GROUPS:
            enabled = getattr(builtin, group_name, True)
            if enabled:
                self.enable_group(group_name)
            else:
                self.disable_group(group_name)

        # 应用别名
        for alias, target in config.aliases.items():
            self.register_alias(alias, target)

        # 注册外部工具
        for ext in config.external:
            try:
                module = importlib.import_module(ext.module)
                for tool_name in ext.tools:
                    tool_func = getattr(module, tool_name, None)
                    if tool_func:
                        self.register(tool_name, tool_func)
                        logger.info(f"已加载外部工具: {ext.module}.{tool_name}")
                    else:
                        logger.warning(f"外部工具 {tool_name} 在模块 {ext.module} 中不存在")
            except ImportError as e:
                logger.warning(f"无法加载外部工具模块 {ext.module}: {e}")

    def reset(self) -> None:
        """重置注册表到初始状态"""
        self._tools.clear()
        self._aliases.clear()
        self._enabled_groups.clear()
        self._disabled_tools.clear()
        self._register_all_builtin_tools()
        logger.debug("工具注册表已重置")


# 全局单例
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表单例"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def get_tool(name: str) -> Optional[Callable]:
    """
    便捷函数：按名称获取工具

    Args:
        name: 工具名称或别名

    Returns:
        工具函数
    """
    return get_tool_registry().get(name)


def get_tools(names: List[str]) -> List[Callable]:
    """
    便捷函数：批量获取工具

    Args:
        names: 工具名称列表

    Returns:
        工具函数列表
    """
    return get_tool_registry().get_many(names)
