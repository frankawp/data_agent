"""
SubAgent 配置模块

定义各个专业子代理的配置，供 multi_agent.py 使用。
"""

from .data_collector import DATA_COLLECTOR_CONFIG
from .data_analyzer import DATA_ANALYZER_CONFIG
from .report_writer import REPORT_WRITER_CONFIG

__all__ = [
    "DATA_COLLECTOR_CONFIG",
    "DATA_ANALYZER_CONFIG",
    "REPORT_WRITER_CONFIG",
]
