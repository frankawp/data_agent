"""配置管理模块"""

from .settings import Settings, get_settings
from .prompts import SYSTEM_PROMPTS
from .modes import (
    ModeManager,
    ModeConfig,
    get_mode_manager,
    PlanModeValue,
    PreviewLimitValue,
    MODE_DEFINITIONS,
)
from .schema import (
    AgentSystemConfig,
    SubAgentConfig,
    LLMProfile,
    LLMConfig,
    ToolsConfig,
    HotReloadConfig,
)
from .loader import (
    ConfigLoader,
    get_config_loader,
    get_agent_config,
    reload_agent_config,
)
from .watcher import (
    ConfigWatcher,
    get_config_watcher,
    start_config_watcher,
    stop_config_watcher,
)

__all__ = [
    # 基础配置
    "Settings",
    "get_settings",
    "SYSTEM_PROMPTS",
    # 模式管理
    "ModeManager",
    "ModeConfig",
    "get_mode_manager",
    "PlanModeValue",
    "PreviewLimitValue",
    "MODE_DEFINITIONS",
    # Agent 配置 Schema
    "AgentSystemConfig",
    "SubAgentConfig",
    "LLMProfile",
    "LLMConfig",
    "ToolsConfig",
    "HotReloadConfig",
    # 配置加载器
    "ConfigLoader",
    "get_config_loader",
    "get_agent_config",
    "reload_agent_config",
    # 热重载监听
    "ConfigWatcher",
    "get_config_watcher",
    "start_config_watcher",
    "stop_config_watcher",
]
