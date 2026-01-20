"""
数据采集 SubAgent 配置

负责从数据库采集数据，执行 SQL 查询和表结构探索。

注意：提示词已迁移到 config/prompts/data_collector.md
此处仅保留简短的默认提示词作为无配置时的 fallback。
"""

from ...tools import list_tables, describe_table, execute_sql, execute_python_safe

# 简短的 fallback 提示词（无配置文件时使用）
# 完整提示词请见 config/prompts/data_collector.md
DEFAULT_DATA_COLLECTOR_PROMPT = "你是一个数据采集代理，负责从数据库或文件获取数据。"

DATA_COLLECTOR_CONFIG = {
    "name": "data-collector",
    "description": "从数据库或上传文件采集数据。用于 SQL 查询、表结构探索、读取 Excel/CSV 文件。",
    "system_prompt": DEFAULT_DATA_COLLECTOR_PROMPT,
    "tools": [list_tables, describe_table, execute_sql, execute_python_safe],
}
