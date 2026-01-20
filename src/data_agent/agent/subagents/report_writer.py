"""
报告生成 SubAgent 配置

负责生成可视化图表和分析报告。

注意：提示词已迁移到 config/prompts/report_writer.md
此处仅保留简短的默认提示词作为无配置时的 fallback。
"""

from ...tools import execute_python_safe

# 简短的 fallback 提示词（无配置文件时使用）
# 完整提示词请见 config/prompts/report_writer.md
DEFAULT_REPORT_WRITER_PROMPT = "你是一个报告生成代理，负责创建数据可视化和分析报告。"

REPORT_WRITER_CONFIG = {
    "name": "report-writer",
    "description": "生成可视化图表和分析报告。用于创建数据可视化、格式化分析结果、生成专业报告。",
    "system_prompt": DEFAULT_REPORT_WRITER_PROMPT,
    "tools": [execute_python_safe],
}
