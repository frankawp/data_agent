"""
配置加载器

负责从 YAML 文件加载配置，支持：
1. 环境变量替换 (${VAR} 或 ${VAR:default})
2. 多配置源合并（项目默认 → 用户自定义）
3. 提示词文件加载
4. 配置验证
5. 热重载回调
"""

import logging
import os
import re
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from .schema import AgentSystemConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    配置加载器

    单例模式，负责加载和管理 Agent 系统配置。

    使用示例:
        loader = get_config_loader()
        config = loader.config

        # 热重载
        loader.reload()

        # 注册重载回调
        loader.register_callback(lambda cfg: print("配置已重载"))
    """

    # 默认配置文件搜索路径（按优先级从低到高）
    DEFAULT_CONFIG_PATHS = [
        Path(__file__).parent / "agents.yaml",  # 项目默认配置
        Path.home() / ".data_agent" / "agents.yaml",  # 用户自定义配置
    ]

    _instance: Optional["ConfigLoader"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ConfigLoader":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._config: Optional[AgentSystemConfig] = None
        self._config_path: Optional[Path] = None
        self._callbacks: List[Callable[[AgentSystemConfig], None]] = []
        self._initialized = True

        # 初始化时加载配置
        self.reload()

    def reload(self, config_path: Optional[Path] = None) -> AgentSystemConfig:
        """
        重新加载配置

        Args:
            config_path: 指定配置文件路径，不指定则按优先级查找

        Returns:
            加载后的配置对象
        """
        # 确定配置文件路径
        if config_path:
            self._config_path = Path(config_path)
        else:
            self._config_path = self._find_config_file()

        # 加载配置
        if self._config_path and self._config_path.exists():
            logger.info(f"加载配置文件: {self._config_path}")
            raw_config = self._load_yaml(self._config_path)
        else:
            logger.info("未找到配置文件，使用默认配置")
            raw_config = {}

        # 环境变量替换
        raw_config = self._substitute_env_vars(raw_config)

        # 验证并创建配置对象
        try:
            self._config = AgentSystemConfig(**raw_config)
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            # 使用默认配置
            self._config = AgentSystemConfig()

        # 加载提示词文件
        self._load_prompt_files()

        # 触发回调
        self._notify_reload()

        return self._config

    def _find_config_file(self) -> Optional[Path]:
        """按优先级查找配置文件"""
        # 环境变量指定
        env_path = os.environ.get("DATA_AGENT_CONFIG")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
            logger.warning(f"环境变量 DATA_AGENT_CONFIG 指定的路径不存在: {env_path}")

        # 按默认路径查找（后面的优先级更高）
        found_path = None
        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                found_path = path

        return found_path

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """加载 YAML 文件"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.error(f"YAML 解析错误: {e}")
            return {}
        except IOError as e:
            logger.error(f"文件读取错误: {e}")
            return {}

    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        递归替换环境变量

        支持格式:
        - ${VAR} - 替换为环境变量值，不存在则为空字符串
        - ${VAR:default} - 替换为环境变量值，不存在则使用默认值
        """
        if isinstance(obj, str):
            # 匹配 ${VAR} 或 ${VAR:default}
            pattern = r"\$\{(\w+)(?::([^}]*))?\}"

            def replacer(match):
                var_name = match.group(1)
                default = match.group(2)
                value = os.environ.get(var_name)
                if value is not None:
                    return value
                return default if default is not None else ""

            return re.sub(pattern, replacer, obj)

        elif isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}

        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]

        return obj

    def _load_prompt_files(self):
        """加载外部提示词文件"""
        if not self._config or not self._config_path:
            return

        config_dir = self._config_path.parent

        # 加载子代理提示词
        for name, subagent in self._config.subagents.items():
            if subagent.prompt_file and not subagent.system_prompt:
                prompt_path = config_dir / subagent.prompt_file
                if prompt_path.exists():
                    try:
                        subagent.system_prompt = prompt_path.read_text(encoding="utf-8")
                        logger.debug(f"加载子代理 {name} 的提示词: {prompt_path}")
                    except IOError as e:
                        logger.warning(f"无法加载提示词文件 {prompt_path}: {e}")
                else:
                    logger.warning(f"提示词文件不存在: {prompt_path}")

        # 加载协调者提示词
        coord = self._config.coordinator
        if coord.prompt_file and not coord.system_prompt:
            prompt_path = config_dir / coord.prompt_file
            if prompt_path.exists():
                try:
                    coord.system_prompt = prompt_path.read_text(encoding="utf-8")
                    logger.debug(f"加载协调者提示词: {prompt_path}")
                except IOError as e:
                    logger.warning(f"无法加载提示词文件 {prompt_path}: {e}")

    def register_callback(self, callback: Callable[[AgentSystemConfig], None]) -> None:
        """
        注册配置重载回调

        Args:
            callback: 配置重载时调用的函数，接收新配置作为参数
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[AgentSystemConfig], None]) -> None:
        """
        取消注册配置重载回调

        Args:
            callback: 要取消的回调函数
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_reload(self):
        """通知所有回调配置已重载"""
        for callback in self._callbacks:
            try:
                callback(self._config)
            except Exception as e:
                logger.error(f"配置重载回调失败: {e}")

    @property
    def config(self) -> AgentSystemConfig:
        """获取当前配置"""
        if self._config is None:
            self.reload()
        return self._config

    @property
    def config_path(self) -> Optional[Path]:
        """获取当前配置文件路径"""
        return self._config_path

    def has_custom_config(self) -> bool:
        """检查是否有自定义配置文件"""
        return self._config_path is not None and self._config_path.exists()

    def has_subagents_config(self) -> bool:
        """检查是否配置了子代理"""
        return bool(self._config and self._config.subagents)


# 全局单例访问函数
_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """获取配置加载器单例"""
    global _loader
    if _loader is None:
        _loader = ConfigLoader()
    return _loader


def get_agent_config() -> AgentSystemConfig:
    """获取 Agent 系统配置"""
    return get_config_loader().config


def reload_agent_config(config_path: Optional[Path] = None) -> AgentSystemConfig:
    """
    重新加载 Agent 系统配置

    Args:
        config_path: 可选的配置文件路径

    Returns:
        重新加载后的配置对象
    """
    return get_config_loader().reload(config_path)
