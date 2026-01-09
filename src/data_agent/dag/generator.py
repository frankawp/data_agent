"""
DAG生成器

根据用户需求生成DAG执行计划。
"""

import json
import logging
import re
from typing import Optional, List

from langchain_core.messages import HumanMessage, SystemMessage

from .models import DAGNode, DAGPlan
from ..agent.zhipu_llm import create_zhipu_llm
from ..config.prompts import PLANNING_PROMPT, DAG_EXAMPLES

logger = logging.getLogger(__name__)


class DAGGenerator:
    """
    DAG生成器

    使用LLM根据用户需求生成DAG执行计划。
    """

    def __init__(self, temperature: float = 0.3):
        """
        初始化DAG生成器

        Args:
            temperature: LLM温度参数，较低值产生更确定的输出
        """
        self.llm = create_zhipu_llm(temperature=temperature)

    def generate(self, user_request: str, context: str = "") -> DAGPlan:
        """
        根据用户需求生成DAG计划

        Args:
            user_request: 用户的数据分析需求
            context: 额外的上下文信息（如数据库表结构等）

        Returns:
            DAGPlan: 生成的执行计划
        """
        # 构建系统提示
        system_prompt = f"{PLANNING_PROMPT}\n\n{DAG_EXAMPLES}"

        # 构建用户提示
        user_prompt = f"用户需求: {user_request}"
        if context:
            user_prompt += f"\n\n上下文信息:\n{context}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # 调用LLM
        response = self.llm.invoke(messages)
        response_text = response.content

        # 解析JSON
        dag_plan = self._parse_response(response_text)

        # 验证DAG
        errors = dag_plan.validate()
        if errors:
            logger.warning(f"DAG验证警告: {errors}")

        return dag_plan

    async def agenerate(self, user_request: str, context: str = "") -> DAGPlan:
        """
        异步生成DAG计划

        Args:
            user_request: 用户的数据分析需求
            context: 额外的上下文信息

        Returns:
            DAGPlan: 生成的执行计划
        """
        system_prompt = f"{PLANNING_PROMPT}\n\n{DAG_EXAMPLES}"

        user_prompt = f"用户需求: {user_request}"
        if context:
            user_prompt += f"\n\n上下文信息:\n{context}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await self.llm.ainvoke(messages)
        response_text = response.content

        dag_plan = self._parse_response(response_text)

        errors = dag_plan.validate()
        if errors:
            logger.warning(f"DAG验证警告: {errors}")

        return dag_plan

    def _parse_response(self, response_text: str) -> DAGPlan:
        """
        解析LLM响应，提取DAG计划

        Args:
            response_text: LLM响应文本

        Returns:
            DAGPlan: 解析出的执行计划
        """
        # 尝试提取JSON块
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # 尝试直接解析整个响应
            json_str = response_text.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            # 返回空计划
            return DAGPlan(name="解析失败", description=str(e))

        # 处理不同的JSON格式
        if isinstance(data, dict):
            if "nodes" in data:
                return DAGPlan.from_dict(data)
            else:
                # 可能是单个节点
                node = DAGNode.from_dict(data)
                return DAGPlan(nodes=[node])
        elif isinstance(data, list):
            # 节点列表
            nodes = [DAGNode.from_dict(n) for n in data]
            return DAGPlan(nodes=nodes)
        else:
            logger.error(f"未知的JSON格式: {type(data)}")
            return DAGPlan(name="格式错误")

    def refine(self, dag_plan: DAGPlan, feedback: str) -> DAGPlan:
        """
        根据用户反馈优化DAG计划

        Args:
            dag_plan: 原始计划
            feedback: 用户反馈

        Returns:
            DAGPlan: 优化后的计划
        """
        system_prompt = """你需要根据用户反馈优化现有的DAG执行计划。

保持原有计划的结构，只修改用户指出的问题。
输出优化后的完整JSON格式DAG计划。"""

        user_prompt = f"""现有计划:
{dag_plan.to_json()}

用户反馈:
{feedback}

请输出优化后的计划（JSON格式）:"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)
        return self._parse_response(response.content)


def create_simple_dag(
    name: str,
    tool: str,
    params: dict,
    description: str = ""
) -> DAGPlan:
    """
    创建简单的单节点DAG

    Args:
        name: 任务名称
        tool: 工具名称
        params: 工具参数
        description: 描述

    Returns:
        DAGPlan: 单节点执行计划
    """
    node = DAGNode(
        id="task_1",
        name=name,
        tool=tool,
        params=params,
    )
    return DAGPlan(
        nodes=[node],
        name=name,
        description=description,
    )


def create_sequential_dag(
    tasks: List[dict],
    name: str = "顺序执行计划"
) -> DAGPlan:
    """
    创建顺序执行的DAG

    Args:
        tasks: 任务列表，每个任务包含name, tool, params
        name: 计划名称

    Returns:
        DAGPlan: 顺序执行计划
    """
    nodes = []
    for i, task in enumerate(tasks):
        node = DAGNode(
            id=f"task_{i+1}",
            name=task["name"],
            tool=task["tool"],
            params=task.get("params", {}),
            dependencies=[f"task_{i}"] if i > 0 else [],
        )
        nodes.append(node)

    return DAGPlan(nodes=nodes, name=name)
