"""
Plan Mode 执行器

负责任务规划、用户确认和分步执行。
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable, Any

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config.modes import get_mode_manager, PlanModeValue


class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"      # 简单：单步操作
    MEDIUM = "medium"      # 中等：2-3步操作
    COMPLEX = "complex"    # 复杂：多步操作，需要规划


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """计划步骤"""
    index: int
    description: str
    tool_hint: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None


@dataclass
class ExecutionPlan:
    """执行计划"""
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    complexity: TaskComplexity = TaskComplexity.MEDIUM
    estimated_tools: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = [
            "## 任务目标",
            self.goal,
            "",
            "## 执行步骤",
            ""
        ]

        status_icons = {
            StepStatus.PENDING: "○",
            StepStatus.RUNNING: "→",
            StepStatus.COMPLETED: "✓",
            StepStatus.FAILED: "✗",
            StepStatus.SKIPPED: "⊘",
        }

        for step in self.steps:
            icon = status_icons.get(step.status, "○")
            lines.append(f"{icon} **步骤 {step.index}**: {step.description}")
            if step.tool_hint:
                lines.append(f"   _工具: {step.tool_hint}_")
            lines.append("")  # 步骤之间添加空行

        if self.estimated_tools:
            lines.append("## 预计使用工具")
            lines.append(", ".join(self.estimated_tools))

        return "\n".join(lines)

    def get_progress(self) -> tuple:
        """获取进度信息"""
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        total = len(self.steps)
        return completed, total


class PlanExecutor:
    """
    Plan Mode 执行器

    负责：
    1. 判断任务复杂度
    2. 生成执行计划
    3. 用户确认流程
    4. 分步执行并报告进度
    """

    # 复杂任务关键词
    COMPLEX_KEYWORDS = [
        "分析", "比较", "统计", "趋势", "预测", "训练", "模型",
        "多个", "所有", "全部", "批量", "汇总", "报告", "可视化",
        "关联", "join", "聚合", "group by", "相关性", "回归",
        "分类", "聚类", "机器学习", "深度", "优化"
    ]

    # 简单任务关键词
    SIMPLE_KEYWORDS = [
        "查看", "列出", "显示", "多少", "有哪些", "是什么",
        "show", "list", "describe", "count", "查询", "获取"
    ]

    def __init__(self, console: Console):
        self.console = console
        self.current_plan: Optional[ExecutionPlan] = None
        self._mode_manager = get_mode_manager()

    def should_plan(self, user_input: str) -> bool:
        """
        判断是否需要规划

        根据当前 plan_mode 和任务复杂度决定。
        """
        plan_mode = self._mode_manager.get("plan")

        if plan_mode == PlanModeValue.OFF:
            return False
        elif plan_mode == PlanModeValue.ON:
            return True
        else:  # AUTO
            complexity = self._assess_complexity(user_input)
            return complexity == TaskComplexity.COMPLEX

    def _assess_complexity(self, user_input: str) -> TaskComplexity:
        """评估任务复杂度"""
        input_lower = user_input.lower()

        # 检查复杂任务关键词
        complex_count = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in input_lower)
        simple_count = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in input_lower)

        # 检查输入长度（长查询通常更复杂）
        length_factor = len(user_input) > 100

        # 检查是否包含多个问号或逗号（多个子任务）
        multi_task = (
            user_input.count("，") + user_input.count(",") > 2
            or user_input.count("？") > 1
            or user_input.count("?") > 1
        )

        if complex_count >= 2 or (complex_count >= 1 and (length_factor or multi_task)):
            return TaskComplexity.COMPLEX
        elif simple_count >= 1 and complex_count == 0:
            return TaskComplexity.SIMPLE
        else:
            return TaskComplexity.MEDIUM

    def generate_plan_prompt(self, user_input: str) -> str:
        """
        生成规划提示，让 LLM 输出结构化的计划
        """
        return f"""请为以下数据分析任务生成一个详细的执行计划。

任务: {user_input}

请严格按照以下 JSON 格式输出计划（不要添加其他内容）：
```json
{{
    "goal": "任务的核心目标描述",
    "steps": [
        {{"index": 1, "description": "具体步骤描述", "tool_hint": "预期使用的工具名（可选）"}},
        {{"index": 2, "description": "具体步骤描述", "tool_hint": "预期使用的工具名（可选）"}}
    ],
    "estimated_tools": ["工具1", "工具2"]
}}
```

注意：
1. 每个步骤应该是一个独立的、可执行的操作
2. 步骤之间应有合理的依赖关系
3. tool_hint 可以是: execute_sql, list_tables, describe_table, analyze_dataframe, statistical_analysis, train_model, predict 等
4. 步骤数量建议在 2-6 步之间
"""

    def parse_plan_response(self, response: str, original_goal: str) -> Optional[ExecutionPlan]:
        """解析 LLM 返回的计划"""
        # 提取 JSON 块
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接查找 JSON 对象
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                return None
            json_str = json_match.group()

        try:
            data = json.loads(json_str)
            steps = [
                PlanStep(
                    index=s.get("index", i + 1),
                    description=s["description"],
                    tool_hint=s.get("tool_hint")
                )
                for i, s in enumerate(data.get("steps", []))
            ]

            if not steps:
                return None

            return ExecutionPlan(
                goal=data.get("goal", original_goal),
                steps=steps,
                complexity=TaskComplexity.COMPLEX,
                estimated_tools=data.get("estimated_tools", [])
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def display_plan(self, plan: ExecutionPlan) -> None:
        """显示执行计划"""
        self.console.print()
        self.console.print(Panel(
            Markdown(plan.to_markdown()),
            title="[bold yellow]执行计划[/bold yellow]",
            border_style="yellow"
        ))

    def confirm_plan(self, plan: ExecutionPlan) -> bool:
        """
        请求用户确认计划

        Returns:
            True: 用户确认执行
            False: 用户取消
        """
        self.display_plan(plan)
        self.console.print()

        return Confirm.ask("是否按此计划执行？", default=True)

    def update_step_status(
        self,
        plan: ExecutionPlan,
        step_index: int,
        status: StepStatus,
        result: Optional[str] = None
    ) -> None:
        """更新步骤状态"""
        for step in plan.steps:
            if step.index == step_index:
                step.status = status
                if result:
                    step.result = result
                break

    def display_progress(self, plan: ExecutionPlan) -> None:
        """显示执行进度"""
        completed, total = plan.get_progress()

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("状态", width=3)
        table.add_column("步骤", style="white")

        status_styles = {
            StepStatus.PENDING: ("○", "dim"),
            StepStatus.RUNNING: ("→", "yellow"),
            StepStatus.COMPLETED: ("✓", "green"),
            StepStatus.FAILED: ("✗", "red"),
            StepStatus.SKIPPED: ("⊘", "dim"),
        }

        for step in plan.steps:
            icon, style = status_styles.get(step.status, ("○", "dim"))
            table.add_row(
                f"[{style}]{icon}[/{style}]",
                f"[{style}]步骤 {step.index}: {step.description}[/{style}]"
            )

        self.console.print(Panel(
            table,
            title=f"[bold]进度 {completed}/{total}[/bold]",
            border_style="blue"
        ))

    def create_execution_prompt(self, plan: ExecutionPlan, step: PlanStep) -> str:
        """
        为特定步骤创建执行提示
        """
        context = f"你正在执行一个数据分析任务的第 {step.index} 步。\n\n"
        context += f"总体目标: {plan.goal}\n\n"
        context += f"当前步骤: {step.description}\n"

        if step.tool_hint:
            context += f"建议使用工具: {step.tool_hint}\n"

        # 添加之前步骤的结果作为上下文
        previous_results = []
        for s in plan.steps:
            if s.index < step.index and s.status == StepStatus.COMPLETED and s.result:
                previous_results.append(f"步骤 {s.index} 结果: {s.result[:200]}...")

        if previous_results:
            context += "\n之前步骤的结果:\n" + "\n".join(previous_results)

        context += "\n\n请执行当前步骤并返回结果。"

        return context

    def summarize_results(self, plan: ExecutionPlan) -> str:
        """汇总所有步骤的结果"""
        summary_parts = [f"## 任务完成: {plan.goal}\n"]

        for step in plan.steps:
            if step.status == StepStatus.COMPLETED:
                summary_parts.append(f"### 步骤 {step.index}: {step.description}")
                if step.result:
                    # 限制每个结果的长度
                    result_preview = step.result[:500]
                    if len(step.result) > 500:
                        result_preview += "..."
                    summary_parts.append(result_preview)
                summary_parts.append("")
            elif step.status == StepStatus.FAILED:
                summary_parts.append(f"### 步骤 {step.index}: {step.description} [失败]")
                if step.result:
                    summary_parts.append(f"错误: {step.result}")
                summary_parts.append("")

        return "\n".join(summary_parts)
