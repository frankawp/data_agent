"""
配置文件监听器

监听配置文件变化，支持热重载。
使用 watchdog 库实现文件系统监听。
"""

import logging
import threading
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

# watchdog 是可选依赖
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更处理器"""

    def __init__(self, callback: Callable, debounce_ms: int = 1000):
        """
        初始化处理器

        Args:
            callback: 文件变更时的回调函数
            debounce_ms: 防抖延迟（毫秒）
        """
        self.callback = callback
        self.debounce_ms = debounce_ms
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return

        # 只处理 .yaml, .yml, .md 文件
        path = Path(event.src_path)
        if path.suffix not in (".yaml", ".yml", ".md"):
            return

        logger.debug(f"检测到配置文件变更: {path}")
        self._debounced_callback()

    def on_created(self, event):
        """文件创建事件处理"""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix in (".yaml", ".yml", ".md"):
            logger.debug(f"检测到配置文件创建: {path}")
            self._debounced_callback()

    def _debounced_callback(self):
        """防抖处理"""
        with self._lock:
            if self._timer:
                self._timer.cancel()

            self._timer = threading.Timer(
                self.debounce_ms / 1000, self._execute_callback
            )
            self._timer.start()

    def _execute_callback(self):
        """执行回调"""
        try:
            logger.info("执行配置热重载")
            self.callback()
        except Exception as e:
            logger.error(f"配置重载回调失败: {e}")


class ConfigWatcher:
    """
    配置文件监听器

    监听指定路径的配置文件变化，触发回调函数。

    使用示例:
        watcher = get_config_watcher()

        def on_reload():
            print("配置已重载")

        watcher.start(
            watch_paths=["config/agents.yaml", "config/prompts/"],
            callback=on_reload,
        )

        # 停止监听
        watcher.stop()
    """

    def __init__(self):
        self._observer: Optional[Observer] = None
        self._handlers: List[ConfigFileHandler] = []
        self._running = False

    def start(
        self,
        watch_paths: List[str],
        callback: Callable,
        debounce_ms: int = 1000,
    ) -> bool:
        """
        启动监听

        Args:
            watch_paths: 要监听的路径列表（支持文件和目录）
            callback: 文件变更时的回调函数
            debounce_ms: 防抖延迟（毫秒）

        Returns:
            是否成功启动
        """
        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog 未安装，热重载功能不可用。运行 pip install watchdog 安装。")
            return False

        if self._running:
            self.stop()

        self._observer = Observer()
        handler = ConfigFileHandler(callback, debounce_ms)
        self._handlers.append(handler)

        watched_count = 0
        for path_str in watch_paths:
            path = Path(path_str)

            # 如果是相对路径，相对于配置目录解析
            if not path.is_absolute():
                from .loader import get_config_loader

                loader = get_config_loader()
                if loader.config_path:
                    path = loader.config_path.parent / path
                else:
                    # 使用默认配置目录
                    path = Path(__file__).parent / path

            if path.exists():
                watch_dir = path if path.is_dir() else path.parent
                self._observer.schedule(handler, str(watch_dir), recursive=True)
                logger.info(f"开始监听配置文件: {watch_dir}")
                watched_count += 1
            else:
                logger.warning(f"监听路径不存在: {path}")

        if watched_count == 0:
            logger.warning("没有有效的监听路径")
            return False

        self._observer.start()
        self._running = True
        logger.info("配置热重载监听已启动")
        return True

    def stop(self):
        """停止监听"""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

        self._handlers.clear()
        self._running = False
        logger.info("配置热重载监听已停止")

    @property
    def is_running(self) -> bool:
        """检查监听是否运行中"""
        return self._running

    @property
    def is_available(self) -> bool:
        """检查 watchdog 是否可用"""
        return WATCHDOG_AVAILABLE


# 全局监听器实例
_watcher: Optional[ConfigWatcher] = None


def get_config_watcher() -> ConfigWatcher:
    """获取配置监听器单例"""
    global _watcher
    if _watcher is None:
        _watcher = ConfigWatcher()
    return _watcher


def start_config_watcher(callback: Optional[Callable] = None) -> bool:
    """
    启动配置热重载监听

    根据配置文件中的 hot_reload 设置自动启动监听。

    Args:
        callback: 可选的额外回调函数

    Returns:
        是否成功启动
    """
    from .loader import get_config_loader, reload_agent_config

    loader = get_config_loader()
    config = loader.config
    hot_reload = config.hot_reload

    if not hot_reload.enabled:
        logger.debug("热重载未启用")
        return False

    watcher = get_config_watcher()

    def on_change():
        """配置变更处理"""
        reload_agent_config()
        if callback:
            callback()

    return watcher.start(
        watch_paths=hot_reload.watch_paths,
        callback=on_change,
        debounce_ms=hot_reload.debounce_ms,
    )


def stop_config_watcher():
    """停止配置热重载监听"""
    watcher = get_config_watcher()
    if watcher.is_running:
        watcher.stop()
