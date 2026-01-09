"""
DAG执行器

负责执行DAG计划中的任务节点。
"""

import asyncio
import logging
import time
from typing import Dict, Any, Callable, Optional

from ..dag.models import DAGPlan, DAGNode, NodeStatus
from ..tools import (
    execute_sql, query_with_duckdb, query_parquet,
    execute_python_safe,
    analyze_dataframe, statistical_analysis, analyze_large_dataset,
    train_model, predict, evaluate_model,
    create_graph, graph_analysis,
)

logger = logging.getLogger(__name__)


class DAGExecutor:
    """
    DAG执行器

    按拓扑顺序执行DAG计划中的任务。
    """

    def __init__(self, parallel: bool = True):
        """
        初始化执行器

        Args:
            parallel: 是否并行执行无依赖的任务
        """
        self.parallel = parallel
        self._tool_map: Dict[str, Callable] = self._build_tool_map()
        self._results: Dict[str, Any] = {}

    def _build_tool_map(self) -> Dict[str, Callable]:
        """构建工具名称到函数的映射"""
        return {
            # SQL工具
            "execute_sql": execute_sql,
            "query_with_duckdb": query_with_duckdb,
            "query_parquet": query_parquet,

            # Python工具
            "execute_python_safe": execute_python_safe,

            # 数据分析工具
            "analyze_dataframe": analyze_dataframe,
            "statistical_analysis": statistical_analysis,
            "analyze_large_dataset": analyze_large_dataset,

            # 机器学习工具
            "train_model": train_model,
            "predict": predict,
            "evaluate_model": evaluate_model,

            # 图分析工具
            "create_graph": create_graph,
            "graph_analysis": graph_analysis,
        }

    def execute(
        self,
        dag: DAGPlan,
        on_node_start: Optional[Callable[[DAGNode], None]] = None,
        on_node_complete: Optional[Callable[[DAGNode], None]] = None,
    ) -> Dict[str, Any]:
        """
        同步执行DAG

        Args:
            dag: DAG计划
            on_node_start: 节点开始执行时的回调
            on_node_complete: 节点执行完成时的回调

        Returns:
            Dict[str, Any]: 执行结果
        """
        self._results = {}

        # 获取拓扑排序
        try:
            sorted_nodes = dag.topological_sort()
        except ValueError as e:
            logger.error(f"DAG拓扑排序失败: {e}")
            return {"error": str(e)}

        # 逐个执行节点
        for node in sorted_nodes:
            if on_node_start:
                on_node_start(node)

            self._execute_node(node)

            if on_node_complete:
                on_node_complete(node)

            # 如果节点失败，停止执行
            if node.status == NodeStatus.FAILED:
                logger.error(f"节点 {node.id} 执行失败，停止执行")
                break

        return self._results

    async def aexecute(
        self,
        dag: DAGPlan,
        on_node_start: Optional[Callable[[DAGNode], None]] = None,
        on_node_complete: Optional[Callable[[DAGNode], None]] = None,
    ) -> Dict[str, Any]:
        """
        异步执行DAG

        支持并行执行无依赖的任务。

        Args:
            dag: DAG计划
            on_node_start: 节点开始执行时的回调
            on_node_complete: 节点执行完成时的回调

        Returns:
            Dict[str, Any]: 执行结果
        """
        self._results = {}
        completed_nodes = set()

        while True:
            # 获取当前可执行的节点
            ready_nodes = [
                node for node in dag.nodes
                if node.status == NodeStatus.PENDING
                and node.is_ready(completed_nodes)
            ]

            if not ready_nodes:
                # 检查是否还有运行中的节点
                running = [n for n in dag.nodes if n.status == NodeStatus.RUNNING]
                if not running:
                    break
                await asyncio.sleep(0.1)
                continue

            if self.parallel:
                # 并行执行
                tasks = []
                for node in ready_nodes:
                    if on_node_start:
                        on_node_start(node)
                    tasks.append(self._aexecute_node(node))

                await asyncio.gather(*tasks)

                for node in ready_nodes:
                    if node.status == NodeStatus.COMPLETED:
                        completed_nodes.add(node.id)
                    if on_node_complete:
                        on_node_complete(node)
            else:
                # 顺序执行
                for node in ready_nodes:
                    if on_node_start:
                        on_node_start(node)

                    await self._aexecute_node(node)

                    if node.status == NodeStatus.COMPLETED:
                        completed_nodes.add(node.id)
                    if on_node_complete:
                        on_node_complete(node)

            # 检查是否有失败的节点
            failed = [n for n in dag.nodes if n.status == NodeStatus.FAILED]
            if failed:
                logger.error(f"执行失败: {[n.id for n in failed]}")
                break

        return self._results

    def _execute_node(self, node: DAGNode):
        """
        执行单个节点

        Args:
            node: DAG节点
        """
        node.status = NodeStatus.RUNNING
        start_time = time.time()

        try:
            # 获取工具函数
            tool_func = self._tool_map.get(node.tool)
            if tool_func is None:
                raise ValueError(f"未知的工具: {node.tool}")

            # 替换参数中的变量引用
            params = self._resolve_params(node.params)

            # 执行工具
            result = tool_func.invoke(params)

            # 更新节点状态
            node.status = NodeStatus.COMPLETED
            node.result = result
            node.execution_time = time.time() - start_time

            # 保存结果
            self._results[node.id] = result

            logger.info(f"节点 {node.id} 执行成功")

        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            node.execution_time = time.time() - start_time

            self._results[node.id] = {"error": str(e)}

            logger.error(f"节点 {node.id} 执行失败: {e}")

    async def _aexecute_node(self, node: DAGNode):
        """
        异步执行单个节点

        Args:
            node: DAG节点
        """
        node.status = NodeStatus.RUNNING
        start_time = time.time()

        try:
            tool_func = self._tool_map.get(node.tool)
            if tool_func is None:
                raise ValueError(f"未知的工具: {node.tool}")

            params = self._resolve_params(node.params)

            # 异步执行
            if asyncio.iscoroutinefunction(tool_func.invoke):
                result = await tool_func.ainvoke(params)
            else:
                # 在线程池中执行同步函数
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, tool_func.invoke, params)

            node.status = NodeStatus.COMPLETED
            node.result = result
            node.execution_time = time.time() - start_time

            self._results[node.id] = result

            logger.info(f"节点 {node.id} 执行成功")

        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            node.execution_time = time.time() - start_time

            self._results[node.id] = {"error": str(e)}

            logger.error(f"节点 {node.id} 执行失败: {e}")

    def _resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析参数中的变量引用

        支持引用前序节点的结果，格式: ${node_id}

        Args:
            params: 原始参数

        Returns:
            Dict[str, Any]: 解析后的参数
        """
        import re

        resolved = {}
        for key, value in params.items():
            if isinstance(value, str):
                # 查找 ${node_id} 格式的引用
                def replace_ref(match):
                    ref_id = match.group(1)
                    return str(self._results.get(ref_id, match.group(0)))

                resolved[key] = re.sub(r"\$\{(\w+)\}", replace_ref, value)
            else:
                resolved[key] = value

        return resolved

    def get_results(self) -> Dict[str, Any]:
        """获取所有执行结果"""
        return self._results.copy()


def execute_dag(
    dag: DAGPlan,
    parallel: bool = True,
    on_progress: Optional[Callable[[DAGNode], None]] = None,
) -> Dict[str, Any]:
    """
    便捷函数：执行DAG

    Args:
        dag: DAG计划
        parallel: 是否并行执行
        on_progress: 进度回调

    Returns:
        Dict[str, Any]: 执行结果
    """
    executor = DAGExecutor(parallel=parallel)
    return executor.execute(dag, on_node_complete=on_progress)


async def aexecute_dag(
    dag: DAGPlan,
    parallel: bool = True,
    on_progress: Optional[Callable[[DAGNode], None]] = None,
) -> Dict[str, Any]:
    """
    便捷函数：异步执行DAG

    Args:
        dag: DAG计划
        parallel: 是否并行执行
        on_progress: 进度回调

    Returns:
        Dict[str, Any]: 执行结果
    """
    executor = DAGExecutor(parallel=parallel)
    return await executor.aexecute(dag, on_node_complete=on_progress)
