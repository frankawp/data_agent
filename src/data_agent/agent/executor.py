"""DAG执行器 - 负责执行DAG计划"""

import asyncio
import json
from typing import Dict, Any, List
from ..dag.models import DAGPlan, DAGNode
from ..tools.sql_tools import SQL_TOOLS
from ..tools.python_tools import PYTHON_TOOLS
from ..tools.data_tools import DATA_TOOLS
from ..tools.ml_tools import ML_TOOLS
from ..tools.graph_tools import GRAPH_TOOLS


class DAGExecutor:
    """DAG执行器

    负责按拓扑顺序执行DAG节点
    """

    def __init__(self, db_connection: str = None):
        """初始化执行器

        Args:
            db_connection: 数据库连接字符串（可选）
        """
        self.db_connection = db_connection
        self.tool_registry = self._build_tool_registry()
        self.execution_data = {}  # 存储节点的执行结果

    def _build_tool_registry(self) -> Dict[str, Any]:
        """构建工具注册表

        Returns:
            工具名称到工具函数的映射
        """
        registry = {}

        # 注册所有工具
        for tool in SQL_TOOLS + PYTHON_TOOLS + DATA_TOOLS + ML_TOOLS + GRAPH_TOOLS:
            registry[tool.name] = tool

        return registry

    async def execute_dag(
        self,
        dag: DAGPlan,
        progress_callback = None
    ) -> List[Dict[str, Any]]:
        """执行DAG

        Args:
            dag: DAG计划实例
            progress_callback: 进度回调函数（可选）

        Returns:
            执行结果列表
        """
        results = []

        try:
            # 获取拓扑排序的节点
            sorted_nodes = dag.topological_sort()

            # 按顺序执行每个节点
            for i, node in enumerate(sorted_nodes, 1):
                if progress_callback:
                    await progress_callback(i, len(sorted_nodes), node)

                # 执行节点
                result = await self.execute_node(node, self.execution_data)
                results.append({
                    "node_id": node.id,
                    "node_name": node.name,
                    "success": result.get("success", False),
                    "result": result
                })

                # 保存执行结果
                self.execution_data[node.id] = result

                # 如果执行失败且节点是关键节点，停止执行
                if not result.get("success", False):
                    error_msg = result.get("error", "未知错误")
                    results.append({
                        "node_id": node.id,
                        "error": f"节点执行失败: {error_msg}"
                    })
                    break

            return results

        except Exception as e:
            return [{
                "success": False,
                "error": str(e),
                "message": "DAG执行过程中发生异常"
            }]

    async def execute_node(
        self,
        node: DAGNode,
        execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个节点

        Args:
            node: DAG节点
            execution_data: 已执行的节点数据

        Returns:
            执行结果
        """
        try:
            # 检查依赖是否满足
            for dep_id in node.dependencies:
                if dep_id not in execution_data:
                    return {
                        "success": False,
                        "error": f"依赖节点 {dep_id} 尚未执行"
                    }

            # 获取工具
            if node.tool not in self.tool_registry:
                return {
                    "success": False,
                    "error": f"未知的工具: {node.tool}"
                }

            tool = self.tool_registry[node.tool]

            # 准备输入参数
            inputs = self._prepare_inputs(node, execution_data)

            # 执行工具
            if asyncio.iscoroutinefunction(tool.func):
                result = await tool.func(**inputs)
            else:
                result = tool.func(**inputs)

            # 解析结果
            if isinstance(result, str):
                try:
                    result_dict = json.loads(result)
                    return result_dict
                except:
                    return {
                        "success": True,
                        "output": result
                    }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _prepare_inputs(
        self,
        node: DAGNode,
        execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备节点的输入参数

        Args:
            node: DAG节点
            execution_data: 已执行的节点数据

        Returns:
            准备好的输入参数
        """
        inputs = node.inputs.copy()

        # 如果需要数据库连接
        if self.db_connection and 'database_url' not in inputs:
            # 检查工具是否需要数据库连接
            if node.tool in ['sql_query', 'sql_schema', 'sql_tables']:
                inputs['database_url'] = self.db_connection

        # 如果节点有依赖，将依赖节点的结果作为输入
        if node.dependencies:
            # 合并所有依赖节点的数据
            dep_data = {}
            for dep_id in node.dependencies:
                if dep_id in execution_data:
                    dep_data[dep_id] = execution_data[dep_id]

            # 将依赖数据添加到输入中
            if dep_data:
                inputs['dependencies_data'] = json.dumps(dep_data, ensure_ascii=False)

        return inputs

    async def execute_dag_parallel(
        self,
        dag: DAGPlan,
        progress_callback = None
    ) -> List[Dict[str, Any]]:
        """并行执行DAG（尽可能并行执行无依赖关系的节点）

        Args:
            dag: DAG计划实例
            progress_callback: 进度回调函数（可选）

        Returns:
            执行结果列表
        """
        results = []

        try:
            # 获取执行层级
            levels = dag.get_execution_order()
            total_nodes = len(dag.nodes)
            executed_count = 0

            # 按层级执行（同一层级的节点可以并行）
            for level_num, level_nodes in enumerate(levels, 1):
                # 并行执行当前层级的所有节点
                tasks = []
                for node_id in level_nodes:
                    node = dag.get_node_by_id(node_id)
                    if node:
                        tasks.append(self.execute_node(node, self.execution_data))

                # 等待所有任务完成
                level_results = await asyncio.gather(*tasks, return_exceptions=True)

                # 处理结果
                for i, node_id in enumerate(level_nodes):
                    node = dag.get_node_by_id(node_id)
                    result = level_results[i]

                    if isinstance(result, Exception):
                        result = {
                            "success": False,
                            "error": str(result)
                        }

                    results.append({
                        "node_id": node_id,
                        "node_name": node.name if node else node_id,
                        "success": result.get("success", False),
                        "result": result
                    })

                    self.execution_data[node_id] = result
                    executed_count += 1

                    if progress_callback:
                        await progress_callback(executed_count, total_nodes, node)

                # 检查是否有失败的节点
                if any(not r.get("success", False) for r in level_results):
                    # 如果有失败，停止执行后续层级
                    break

            return results

        except Exception as e:
            return [{
                "success": False,
                "error": str(e),
                "message": "DAG并行执行过程中发生异常"
            }]
