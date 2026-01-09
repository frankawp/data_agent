"""DAG生成器 - 将用户需求转换为执行计划"""

import json
import uuid
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from .models import DAGPlan, DAGNode


class DAGGenerator:
    """根据用户需求生成DAG执行计划"""

    def __init__(self, model: ChatAnthropic):
        """初始化DAG生成器

        Args:
            model: LangChain语言模型实例
        """
        self.model = model
        self.available_tools = self._get_available_tools()

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取所有可用工具的描述

        Returns:
            工具描述列表
        """
        return [
            {
                "name": "sql_query",
                "description": "执行SQL查询，从数据库提取数据",
                "use_cases": ["从数据库查询数据", "数据过滤", "数据聚合"],
                "category": "data_extraction"
            },
            {
                "name": "sql_schema",
                "description": "获取数据库表结构信息",
                "use_cases": ["了解数据库结构", "查看列信息"],
                "category": "data_exploration"
            },
            {
                "name": "python_execute",
                "description": "执行Python代码进行自定义计算和转换",
                "use_cases": ["数据转换", "自定义计算", "复杂逻辑处理"],
                "category": "data_transformation"
            },
            {
                "name": "data_analyze",
                "description": "使用pandas/scipy进行数据分析",
                "use_cases": ["统计分析", "相关性分析", "分布分析", "异常值检测", "缺失值分析"],
                "category": "data_analysis"
            },
            {
                "name": "data_transform",
                "description": "使用pandas进行数据清洗和转换",
                "use_cases": ["过滤数据", "排序", "删除列", "填充缺失值"],
                "category": "data_transformation"
            },
            {
                "name": "ml_train",
                "description": "训练机器学习模型（sklearn）",
                "use_cases": ["分类", "回归", "聚类"],
                "category": "machine_learning"
            },
            {
                "name": "graph_analyze",
                "description": "进行图分析（networkx）",
                "use_cases": ["最短路径", "中心性分析", "社区发现", "PageRank"],
                "category": "graph_analysis"
            }
        ]

    async def generate_dag(
        self,
        user_goal: str,
        conversation_history: List[str],
        db_info: Dict[str, Any] = None
    ) -> DAGPlan:
        """生成DAG计划

        Args:
            user_goal: 用户目标描述
            conversation_history: 对话历史
            db_info: 数据库信息（可选）

        Returns:
            DAGPlan实例
        """
        # 构建系统提示词
        system_prompt = self._build_system_prompt()

        # 构建用户消息
        user_message = self._build_user_message(user_goal, conversation_history, db_info)

        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{user_input}")
        ])

        # 调用LLM
        chain = prompt | self.model
        response = await chain.ainvoke({"user_input": user_message})

        # 解析响应
        try:
            # 尝试从响应中提取JSON
            content = response.content
            # 移除可能的markdown代码块标记
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            dag_data = json.loads(content)
            return self._parse_dag_data(dag_data, user_goal)

        except Exception as e:
            # 如果解析失败，返回一个简单的DAG
            return self._create_fallback_dag(user_goal, str(e))

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_desc = "\n".join([
            f"- {tool['name']}: {tool['description']}\n  用途: {', '.join(tool['use_cases'])}"
            for tool in self.available_tools
        ])

        return f"""你是一个数据分析任务规划专家。根据用户需求，生成一个DAG（有向无环图）执行计划。

## 可用工具

{tools_desc}

## DAG生成规则

1. **节点设计**：
   - 每个节点应该是一个清晰、可执行的任务
   - 节点名称应该简洁明了
   - 每个节点必须指定使用的工具
   - 节点之间应该有明确的依赖关系

2. **依赖关系**：
   - 确保DAG没有循环依赖
   - 依赖关系应该反映数据流和任务依赖
   - 合理地安排执行顺序

3. **工具选择**：
   - 根据任务需求选择最合适的工具
   - 考虑工具的组合使用
   - 优先使用高级工具（如data_analyze）而非底层工具（python_execute）

## 输出格式

请以JSON格式返回DAG计划，严格遵循以下结构：

```json
{{
  "name": "DAG名称",
  "description": "DAG的详细描述",
  "nodes": [
    {{
      "id": "node_1",
      "name": "任务名称",
      "tool": "工具名称",
      "description": "任务描述",
      "inputs": {{
        "参数1": "值1",
        "参数2": "值2"
      }},
      "dependencies": []
    }}
  ],
  "edges": [
    {{"from": "node_1", "to": "node_2"}},
    {{"from": "node_2", "to": "node_3"}}
  ],
  "estimated_time": 60
}}
```

## 注意事项

- nodes中的dependencies是依赖节点的ID列表
- edges描述节点之间的连接关系
- estimated_time是预估执行时间（秒）
- 确保生成的DAG是有效的（无循环依赖）
"""

    def _build_user_message(
        self,
        user_goal: str,
        conversation_history: List[str],
        db_info: Dict[str, Any] = None
    ) -> str:
        """构建用户消息"""
        message = f"## 用户目标\n{user_goal}\n\n"

        if conversation_history:
            message += "## 对话历史\n"
            message += "\n".join(conversation_history)
            message += "\n\n"

        if db_info:
            message += "## 数据库信息\n"
            message += json.dumps(db_info, ensure_ascii=False, indent=2)
            message += "\n\n"

        message += "请根据上述信息，生成一个合适的DAG执行计划。"

        return message

    def _parse_dag_data(self, dag_data: Dict[str, Any], user_goal: str) -> DAGPlan:
        """解析DAG数据

        Args:
            dag_data: 原始DAG数据
            user_goal: 用户目标

        Returns:
            DAGPlan实例
        """
        # 解析节点
        nodes = []
        for node_data in dag_data.get("nodes", []):
            node = DAGNode(
                id=node_data["id"],
                name=node_data["name"],
                tool=node_data["tool"],
                description=node_data.get("description"),
                inputs=node_data.get("inputs", {}),
                dependencies=node_data.get("dependencies", [])
            )
            nodes.append(node)

        # 创建DAGPlan
        dag_plan = DAGPlan(
            id=str(uuid.uuid4()),
            name=dag_data.get("name", "数据分析任务"),
            description=dag_data.get("description", user_goal),
            nodes=nodes,
            edges=dag_data.get("edges", []),
            estimated_time=dag_data.get("estimated_time")
        )

        return dag_plan

    def _create_fallback_dag(self, user_goal: str, error: str) -> DAGPlan:
        """创建备用DAG（当LLM解析失败时）

        Args:
            user_goal: 用户目标
            error: 错误信息

        Returns:
            简单的DAGPlan实例
        """
        node = DAGNode(
            id="node_1",
            name="执行Python代码完成任务",
            tool="python_execute",
            description=f"由于自动规划失败（{error}），请手动执行Python代码来完成：{user_goal}",
            inputs={"code": f"# 请在此处编写代码完成: {user_goal}"},
            dependencies=[]
        )

        return DAGPlan(
            id=str(uuid.uuid4()),
            name="手动执行任务",
            description=f"用户目标: {user_goal}",
            nodes=[node],
            edges=[],
            estimated_time=300
        )
