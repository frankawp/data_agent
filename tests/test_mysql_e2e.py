"""
MySQL 数据分析端到端测试

测试内容：
1. 数据库连接
2. SQL 工具
3. DAG 生成器
4. DAG 执行器
5. 完整流程
"""

import sys
sys.path.insert(0, 'src')

from data_agent.tools.sql_tools import list_tables, describe_table, execute_sql
from data_agent.dag.models import DAGPlan, DAGNode
from data_agent.dag.generator import DAGGenerator
from data_agent.dag.visualizer import DAGVisualizer
from data_agent.agent.executor import DAGExecutor


def test_list_tables():
    """测试1: 列出所有表"""
    print("=== 测试1: 列出所有表 ===")
    result = list_tables.invoke({})
    print(result)
    print()
    assert "customer" in result
    print("✓ 通过\n")


def test_describe_table():
    """测试2: 查看表结构"""
    print("=== 测试2: 查看 customer 表结构 ===")
    result = describe_table.invoke({"table_name": "customer"})
    print(result)
    print()
    assert "customer_id" in result
    print("✓ 通过\n")


def test_execute_sql():
    """测试3: 执行 SQL 查询"""
    print("=== 测试3: 执行 SQL 查询 ===")

    # 查询客户总数
    result = execute_sql.invoke({"query": "SELECT COUNT(*) as total FROM customer"})
    print("客户总数:")
    print(result)
    print()

    # 查询前5个客户
    result = execute_sql.invoke({
        "query": "SELECT customer_id, first_name, last_name, email FROM customer LIMIT 5"
    })
    print("前5个客户:")
    print(result)
    print()

    # 按城市统计
    result = execute_sql.invoke({
        "query": """
            SELECT c.city, COUNT(cu.customer_id) as customer_count
            FROM customer cu
            JOIN address a ON cu.address_id = a.address_id
            JOIN city c ON a.city_id = c.city_id
            GROUP BY c.city
            ORDER BY customer_count DESC
            LIMIT 10
        """
    })
    print("按城市统计客户数:")
    print(result)
    print()
    print("✓ 通过\n")


def test_dag_executor():
    """测试4: DAG 执行器"""
    print("=== 测试4: DAG 执行器 ===")

    # 创建 DAG
    dag = DAGPlan(name="测试查询", description="测试 MySQL 查询")

    # 添加节点
    node = DAGNode(
        id="query-1",
        name="查询客户总数",
        tool="execute_sql",
        params={"query": "SELECT COUNT(*) as total FROM customer"},
        dependencies=[]
    )
    dag.add_node(node)

    # 执行
    executor = DAGExecutor()
    results = executor.execute(dag)

    print(f"节点状态: {node.status}")
    print(f"节点结果: {node.result}")
    print()

    assert node.status.value == "completed"
    assert "599" in node.result
    print("✓ 通过\n")


def test_dag_multi_nodes():
    """测试5: 多节点 DAG 执行"""
    print("=== 测试5: 多节点 DAG 执行 ===")

    dag = DAGPlan(name="客户数据分析", description="分析客户分布")

    # 节点1: 按城市统计
    node1 = DAGNode(
        id="query-city",
        name="按城市统计客户数",
        tool="execute_sql",
        params={"query": """
            SELECT c.city, COUNT(cu.customer_id) as customer_count
            FROM customer cu
            JOIN address a ON cu.address_id = a.address_id
            JOIN city c ON a.city_id = c.city_id
            GROUP BY c.city
            ORDER BY customer_count DESC
            LIMIT 10
        """},
        dependencies=[]
    )
    dag.add_node(node1)

    # 节点2: 租借最多的客户
    node2 = DAGNode(
        id="query-top-customers",
        name="租借最多的客户",
        tool="execute_sql",
        params={"query": """
            SELECT c.customer_id, c.first_name, c.last_name, COUNT(r.rental_id) as rental_count
            FROM customer c
            JOIN rental r ON c.customer_id = r.customer_id
            GROUP BY c.customer_id, c.first_name, c.last_name
            ORDER BY rental_count DESC
            LIMIT 5
        """},
        dependencies=[]
    )
    dag.add_node(node2)

    # 执行
    executor = DAGExecutor()
    results = executor.execute(dag)

    print("节点1结果 - 按城市统计:")
    print(node1.result[:300])
    print()

    print("节点2结果 - 租借最多的客户:")
    print(node2.result)
    print()

    assert all(n.status.value == "completed" for n in dag.nodes)
    print("✓ 通过\n")


def test_dag_generator():
    """测试6: DAG 生成器"""
    print("=== 测试6: DAG 生成器 ===")

    generator = DAGGenerator()
    request = "查询customer表中的客户总数"
    context = "使用MySQL数据库"

    print(f"用户请求: {request}")
    print(f"上下文: {context}")
    print()

    dag = generator.generate(request, context)

    print(f"生成的 DAG:")
    print(f"  名称: {dag.name}")
    print(f"  节点数: {len(dag.nodes)}")
    for node in dag.nodes:
        print(f"  - {node.name} ({node.tool})")
        print(f"    参数: {node.params}")
    print()

    assert len(dag.nodes) >= 1
    print("✓ 通过\n")


def test_dag_visualizer():
    """测试7: DAG 可视化"""
    print("=== 测试7: DAG 可视化 ===")

    dag = DAGPlan(name="测试可视化")

    dag.add_node(DAGNode(id="n1", name="步骤1", tool="execute_sql", params={}))
    dag.add_node(DAGNode(id="n2", name="步骤2", tool="execute_sql", params={}, dependencies=["n1"]))
    dag.add_node(DAGNode(id="n3", name="步骤3", tool="execute_sql", params={}, dependencies=["n1"]))
    dag.add_node(DAGNode(id="n4", name="步骤4", tool="execute_sql", params={}, dependencies=["n2", "n3"]))

    visualizer = DAGVisualizer()
    mermaid = visualizer.to_mermaid(dag)

    print("Mermaid 图:")
    print(mermaid)
    print()

    assert "graph TD" in mermaid
    assert "n1" in mermaid
    print("✓ 通过\n")


def test_e2e_flow():
    """测试8: 端到端完整流程（DAG模式）"""
    print("=" * 60)
    print("测试8: 端到端完整流程（DAG模式）")
    print("=" * 60)
    print()

    # 步骤1: 生成 DAG
    generator = DAGGenerator()
    request = "分析客户数据：1. 查询客户总数 2. 找出租借次数最多的5个客户"
    context = "MySQL数据库，表结构包括customer、rental等表"

    print("【步骤1: 生成 DAG】")
    print(f"用户请求: {request}")
    print()

    dag = generator.generate(request, context)
    print(f"生成了 {len(dag.nodes)} 个任务节点:")
    for i, node in enumerate(dag.nodes, 1):
        print(f"  {i}. {node.name} ({node.tool})")
    print()

    # 步骤2: 可视化
    visualizer = DAGVisualizer()
    mermaid = visualizer.to_mermaid(dag)
    print("【步骤2: Mermaid 可视化】")
    print(mermaid)
    print()

    # 步骤3: 执行
    print("【步骤3: 执行 DAG】")
    executor = DAGExecutor()

    def on_progress(node):
        print(f"  ✓ {node.name}: {node.status.value}")

    results = executor.execute(dag, on_node_complete=on_progress)
    print()

    # 步骤4: 显示结果
    print("【步骤4: 执行结果】")
    for node in dag.nodes:
        print(f"{node.name}:")
        if node.result:
            result_lines = node.result.split("\n")
            for line in result_lines[:8]:
                print(f"  {line}")
            if len(result_lines) > 8:
                print(f"  ... (共 {len(result_lines)} 行)")
        if node.error:
            print(f"  错误: {node.error}")
        print()

    # 检查 SQL 节点是否成功
    sql_nodes = [n for n in dag.nodes if n.tool == "execute_sql"]
    assert all(n.status.value == "completed" for n in sql_nodes), "SQL 节点执行失败"

    print("=" * 60)
    print("✓ 端到端测试通过!")
    print("=" * 60)


def test_agent_tool_calling():
    """测试9: Agent 工具调用模式"""
    from data_agent.agent.core import DataAgent
    from data_agent.state.graph_state import create_initial_state

    print("=" * 60)
    print("测试9: Agent 工具调用模式")
    print("=" * 60)
    print()

    agent = DataAgent()

    # 测试1: 查询客户数
    print("【测试: 查询客户数】")
    state = create_initial_state()
    response, state = agent.chat("查询 customer 表中有多少客户", state)
    print(f"Agent 响应: {response[:200]}...")
    print()

    # 验证工具被调用
    messages = state.get("messages", [])
    tool_called = False
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_called = True
            print(f"✓ 工具被调用: {msg.tool_calls[0]['name']}")
            break

    assert tool_called, "Agent 没有调用工具"
    assert "599" in response, "响应中应包含正确的客户数 599"

    print()
    print("=" * 60)
    print("✓ Agent 工具调用测试通过!")
    print("=" * 60)


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("MySQL 数据分析端到端测试")
    print("=" * 60 + "\n")

    tests = [
        test_list_tables,
        test_describe_table,
        test_execute_sql,
        test_dag_executor,
        test_dag_multi_nodes,
        test_dag_generator,
        test_dag_visualizer,
        test_e2e_flow,
        test_agent_tool_calling,  # 新增: Agent 工具调用测试
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
