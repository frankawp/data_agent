"""
多 Agent 数据分析实现

使用 DeepAgents 框架的 subagents 功能，实现多 Agent 协作的数据分析。
主 Agent 作为协调者，将任务分配给专业的子代理处理。
"""

from typing import Optional

from deepagents import create_deep_agent
from langgraph.graph.state import CompiledStateGraph

from .backend import create_session_backend
from .llm import create_llm
from .middleware import SubAgentToolMonitor, SubAgentCallbackHolder
from .subagents import (
    DATA_COLLECTOR_CONFIG,
    DATA_ANALYZER_CONFIG,
    REPORT_WRITER_CONFIG,
)


# 协调者（主 Agent）的系统提示
COORDINATOR_PROMPT = """你是一个数据分析任务的协调者。

## 职责
1. 理解用户的数据分析需求
2. 将任务分配给合适的专业子代理
3. 汇总各子代理的结果
4. 向用户提供清晰的最终答案

## 文件系统说明

你和子代理可以使用以下虚拟路径访问会话文件：

- `/exports/` - 导出文件目录，所有导出的 CSV、图表等文件都在这里
- `/workspace/` - 工作目录，临时文件和中间结果

**常用操作**：
- `ls("/exports/")` - 列出所有导出文件
- `read_file("/exports/result.csv")` - 读取导出的 CSV 文件
- `glob("*.csv", "/exports/")` - 查找所有 CSV 文件

## 可用子代理

### data-collector
- 功能：从数据库采集数据
- 适用：需要查询数据库、探索表结构、获取原始数据时

### data-analyzer
- 功能：分析数据并提取洞察
- 适用：需要统计分析、机器学习建模、图分析时

### report-writer
- 功能：生成可视化图表和报告
- 适用：需要生成图表、格式化报告、数据可视化时

## 工作流程
1. **理解需求**：分析用户想要什么
2. **任务分解**：确定需要哪些子代理参与
3. **顺序执行**：使用 `task()` 工具调用子代理
   - 通常顺序：采集数据 → 分析数据 → 生成报告
   - 每次只调用一个子代理
4. **结果汇总**：整合各子代理的输出，给用户完整答案

## 使用 task() 工具
调用子代理时，使用 `task()` 工具：
- `agent_name`: 子代理名称（data-collector / data-analyzer / report-writer）
- `task`: 详细的任务描述，包含所有必要的上下文

示例：
```
task(
    agent_name="data-collector",
    task="查询 users 表中最近 30 天注册的用户数据，包括 id, name, created_at 字段"
)
```

## 重要提示
- **复杂任务**：请使用子代理，这样可以保持上下文清洁
- **简单问题**：可以直接回答，无需调用子代理
- **数据传递**：将前一个子代理的关键结果包含在下一个任务描述中
- **结果简洁**：子代理会返回简洁的结果，你需要整合并呈现给用户

## 示例对话

用户："分析用户表的数据分布并生成报告"

你的处理步骤：
1. 调用 data-collector 获取用户数据
2. 调用 data-analyzer 分析数据分布
3. 调用 report-writer 生成可视化报告
4. 汇总结果回复用户
"""


def create_multi_agent(
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    callback_holder: Optional[SubAgentCallbackHolder] = None,
) -> CompiledStateGraph:
    """
    创建多 Agent 数据分析器

    使用 DeepAgents 的 subagents 功能，主 Agent 可以将任务委托给专业子代理。

    Args:
        model: 模型名称，默认使用配置中的模型
        system_prompt: 自定义协调者提示，默认使用内置提示
        callback_holder: 子代理回调持有者，支持动态更新回调函数

    Returns:
        CompiledStateGraph: 编译后的多 Agent 图
    """
    # 初始化 LLM
    llm = create_llm(model=model) if model else create_llm()

    # 为子代理添加工具监听中间件
    def add_monitor(config: dict) -> dict:
        """为子代理配置添加监听中间件"""
        if callback_holder is None:
            return config

        # 创建监听中间件（使用 callback_holder 支持动态回调）
        monitor = SubAgentToolMonitor(
            subagent_name=config["name"],
            callback_holder=callback_holder,
        )

        # 合并已有的中间件
        existing_middleware = config.get("middleware", [])
        return {
            **config,
            "middleware": [monitor] + list(existing_middleware),
        }

    # 定义子代理列表（带监听中间件）
    subagents = [
        add_monitor(DATA_COLLECTOR_CONFIG),
        add_monitor(DATA_ANALYZER_CONFIG),
        add_monitor(REPORT_WRITER_CONFIG),
    ]

    # 创建多 Agent，传入会话后端
    agent = create_deep_agent(
        model=llm,
        system_prompt=system_prompt or COORDINATOR_PROMPT,
        subagents=subagents,
        backend=create_session_backend,  # 使用会话后端工厂函数
    )

    return agent
