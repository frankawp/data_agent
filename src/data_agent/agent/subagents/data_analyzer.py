"""
数据分析 SubAgent 配置

负责数据分析，包括统计分析、机器学习建模和图分析。

注意：提示词已迁移到 config/prompts/data_analyzer.md
此处仅保留简短的默认提示词作为无配置时的 fallback。
"""

from ...tools import (
    execute_python_safe,
    train_model,
    predict,
)

# 简短的 fallback 提示词（无配置文件时使用）
# 完整提示词请见 config/prompts/data_analyzer.md
DEFAULT_DATA_ANALYZER_PROMPT = "你是一个数据分析代理，负责对数据进行统计分析和机器学习。"

DATA_ANALYZER_CONFIG = {
    "name": "data-analyzer",
    "description": "分析数据并提取洞察。用于统计分析、AB测试、相关性分析、机器学习建模。",
    "system_prompt": DEFAULT_DATA_ANALYZER_PROMPT,
    "tools": [
        execute_python_safe,
        train_model,
        predict,
    ],
}
