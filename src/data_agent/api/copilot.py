"""
CopilotKit 集成模块

连接现有 DataAgent 到 CopilotKit，提供 Web 对话能力。
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter

from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, Action

from ..agent.deep_agent import create_data_agent
from ..config.modes import get_mode_manager
from ..tools import (
    execute_sql,
    list_tables,
    describe_table,
    execute_python_safe,
    train_model,
    predict,
    list_models,
    create_graph,
    graph_analysis,
    list_graphs,
)


def create_copilot_actions() -> List[Action]:
    """
    创建 CopilotKit Actions，包装现有工具

    每个 Action 对应一个现有的 LangChain 工具，
    CopilotKit 会在对话中调用这些 actions。
    """
    actions = [
        # SQL 工具
        Action(
            name="execute_sql",
            description="执行 SQL 查询（仅支持 SELECT 语句）",
            parameters=[
                {
                    "name": "query",
                    "type": "string",
                    "description": "SQL 查询语句",
                    "required": True,
                },
                {
                    "name": "database",
                    "type": "string",
                    "description": "数据库标识（可选）",
                    "required": False,
                },
            ],
            handler=lambda query, database="default": execute_sql.invoke(
                {"query": query, "database": database}
            ),
        ),
        Action(
            name="list_tables",
            description="列出数据库中的所有表",
            parameters=[],
            handler=lambda: list_tables.invoke({}),
        ),
        Action(
            name="describe_table",
            description="获取表的结构信息（字段、类型、索引）",
            parameters=[
                {
                    "name": "table_name",
                    "type": "string",
                    "description": "表名",
                    "required": True,
                },
            ],
            handler=lambda table_name: describe_table.invoke({"table_name": table_name}),
        ),
        # Python 执行工具
        Action(
            name="execute_python_safe",
            description="在安全沙箱中执行 Python 代码（可用库：pandas, numpy, scipy, sklearn, matplotlib）",
            parameters=[
                {
                    "name": "code",
                    "type": "string",
                    "description": "要执行的 Python 代码",
                    "required": True,
                },
                {
                    "name": "timeout",
                    "type": "number",
                    "description": "执行超时时间（秒），默认 30",
                    "required": False,
                },
            ],
            handler=lambda code, timeout=30: execute_python_safe.invoke(
                {"code": code, "timeout": timeout}
            ),
        ),
        # 机器学习工具
        Action(
            name="train_model",
            description="训练机器学习模型（支持分类、回归、聚类）",
            parameters=[
                {
                    "name": "data_json",
                    "type": "string",
                    "description": "JSON 格式的训练数据",
                    "required": True,
                },
                {
                    "name": "target_column",
                    "type": "string",
                    "description": "目标列名",
                    "required": True,
                },
                {
                    "name": "model_type",
                    "type": "string",
                    "description": "模型类型（如 RandomForest, LogisticRegression, KMeans 等）",
                    "required": True,
                },
                {
                    "name": "model_id",
                    "type": "string",
                    "description": "模型 ID（可选，用于后续引用）",
                    "required": False,
                },
            ],
            handler=lambda **kwargs: train_model.invoke(kwargs),
        ),
        Action(
            name="predict",
            description="使用已训练的模型进行预测",
            parameters=[
                {
                    "name": "model_id",
                    "type": "string",
                    "description": "模型 ID",
                    "required": True,
                },
                {
                    "name": "data_json",
                    "type": "string",
                    "description": "JSON 格式的预测数据",
                    "required": True,
                },
            ],
            handler=lambda model_id, data_json: predict.invoke(
                {"model_id": model_id, "data_json": data_json}
            ),
        ),
        Action(
            name="list_models",
            description="列出所有已训练的模型",
            parameters=[],
            handler=lambda: list_models.invoke({}),
        ),
        # 图分析工具
        Action(
            name="create_graph",
            description="创建图结构",
            parameters=[
                {
                    "name": "edges_json",
                    "type": "string",
                    "description": "JSON 格式的边列表",
                    "required": True,
                },
                {
                    "name": "directed",
                    "type": "boolean",
                    "description": "是否为有向图",
                    "required": False,
                },
                {
                    "name": "graph_id",
                    "type": "string",
                    "description": "图 ID（可选）",
                    "required": False,
                },
            ],
            handler=lambda **kwargs: create_graph.invoke(kwargs),
        ),
        Action(
            name="graph_analysis",
            description="执行图分析算法（PageRank、中心性、社区发现等）",
            parameters=[
                {
                    "name": "graph_id",
                    "type": "string",
                    "description": "图 ID",
                    "required": True,
                },
                {
                    "name": "algorithms",
                    "type": "string",
                    "description": "要执行的算法列表（逗号分隔）",
                    "required": True,
                },
            ],
            handler=lambda graph_id, algorithms: graph_analysis.invoke(
                {"graph_id": graph_id, "algorithms": algorithms}
            ),
        ),
        Action(
            name="list_graphs",
            description="列出所有已创建的图",
            parameters=[],
            handler=lambda: list_graphs.invoke({}),
        ),
    ]

    return actions


def create_copilot_sdk() -> CopilotKitRemoteEndpoint:
    """
    创建 CopilotKit SDK 实例

    复用现有的工具集，通过 CopilotKit 暴露给前端。
    """
    actions = create_copilot_actions()

    sdk = CopilotKitRemoteEndpoint(
        actions=actions,
    )

    return sdk


# SDK 实例（延迟创建）
_sdk: Optional[CopilotKitRemoteEndpoint] = None


def get_copilot_sdk() -> CopilotKitRemoteEndpoint:
    """获取 CopilotKit SDK 单例"""
    global _sdk
    if _sdk is None:
        _sdk = create_copilot_sdk()
    return _sdk


def setup_copilotkit(app):
    """
    设置 CopilotKit 端点

    在 FastAPI 应用上添加 CopilotKit 处理端点。
    必须在应用启动时调用。

    Args:
        app: FastAPI 应用实例
    """
    sdk = get_copilot_sdk()
    add_fastapi_endpoint(app, sdk, "/copilotkit")
