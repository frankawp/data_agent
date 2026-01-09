"""测试智谱AI集成"""

import asyncio
from data_agent import DataAgent


async def test_zhipu_ai():
    """测试智谱AI连接和对话"""

    print("=" * 60)
    print("测试智谱AI集成")
    print("=" * 60)

    # 创建Agent实例（使用智谱AI）
    agent = DataAgent(
        api_key="a2d9aad92f254c17b3c71495177cc94b.vXbdUFVOvhGZnqf8",
        model_name="glm-4",
        provider="zhipu",
        base_url="https://open.bigmodel.cn/api/paas/v4"
    )

    print("\n✓ Agent创建成功")
    print(f"  Provider: {agent.provider}")
    print(f"  LLM类型: {type(agent.llm).__name__}")

    # 测试简单对话
    print("\n" + "=" * 60)
    print("测试对话功能")
    print("=" * 60)

    user_input = "你好，请简单介绍一下你自己"
    print(f"\n用户: {user_input}")

    try:
        state = await agent.chat(user_input)

        # 获取AI响应
        messages = state.get("messages", [])
        ai_messages = [msg for msg in messages if msg.__class__.__name__ == 'AIMessage']

        if ai_messages:
            last_response = ai_messages[-1].content
            print(f"\nAgent: {last_response}")
            print("\n✓ 对话测试成功")
        else:
            print("\n✗ 未收到AI响应")

    except Exception as e:
        print(f"\n✗ 对话测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_zhipu_ai())
