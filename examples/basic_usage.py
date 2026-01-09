"""基础使用示例"""

import asyncio
from data_agent import DataAgent, DAGPlan, DAGVisualizer


async def main():
    """基础使用示例"""

    # 1. 创建Agent实例
    agent = DataAgent(
        api_key="your-anthropic-api-key",  # 或设置环境变量 ANTHROPIC_API_KEY
        db_connection="mysql+pymysql://user:password@localhost:3306/database"  # 可选
    )

    # 2. 与Agent对话
    state = None
    user_input = "我想分析用户表中最近一个月的注册趋势"

    # 多轮对话
    state = await agent.chat(user_input, state)

    # 查看AI响应
    messages = state["messages"]
    for msg in messages:
        print(f"{msg.__class__.__name__}: {msg.content}\n")

    # 3. 如果生成了DAG，查看DAG计划
    if state.get("dag_plan"):
        dag_plan_dict = state["dag_plan"]
        dag = DAGPlan.from_dict(dag_plan_dict)

        # 可视化DAG
        visualizer = DAGVisualizer()

        print("=" * 60)
        print("DAG执行计划（ASCII格式）")
        print("=" * 60)
        print(visualizer.to_ascii(dag))
        print("\n")

        print("=" * 60)
        print("DAG执行计划（Mermaid格式）")
        print("=" * 60)
        print(visualizer.to_mermaid(dag))
        print("\n")

        # 4. 确认并执行DAG
        state = await agent.confirm_dag(True, state)

        # 使用DAG执行器执行
        from data_agent import DAGExecutor

        executor = DAGExecutor(db_connection=agent.db_connection)
        results = await executor.execute_dag(dag)

        # 查看执行结果
        print("=" * 60)
        print("执行结果")
        print("=" * 60)
        for result in results:
            print(f"节点: {result['node_name']}")
            print(f"成功: {result['success']}")
            print(f"结果: {result.get('result', {})}")
            print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
