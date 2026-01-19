"""
Dagster 数据处理功能端到端测试

测试场景：AB Test 效果指标计算
- 三个分组：6折满额券、15天满额券、对照组
- 计算：拉平倍率、净增、倍率、转化率
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import numpy as np

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def create_test_data():
    """
    创建 AB Test 测试数据

    模拟三组实验数据：
    - 6折满额券组：营销人数 10000
    - 15天满额券组：营销人数 8000
    - 对照组：营销人数 12000
    """
    np.random.seed(42)

    dates = pd.date_range("2024-01-01", periods=7, freq="D")
    groups = ["6折满额券", "15天满额券", "对照组"]
    marketing_counts = {"6折满额券": 10000, "15天满额券": 8000, "对照组": 12000}

    data = []
    for date in dates:
        for group in groups:
            marketing_count = marketing_counts[group]

            # 基础转化率
            if group == "6折满额券":
                base_rate = 0.15  # 最高转化
            elif group == "15天满额券":
                base_rate = 0.12
            else:
                base_rate = 0.10  # 对照组最低

            # 生成指标（加入一些随机波动）
            balance = marketing_count * (500 + np.random.normal(0, 50)) * base_rate
            revenue = balance * 0.05
            visit_count = int(marketing_count * (base_rate + np.random.normal(0, 0.02)))
            loan_count = int(visit_count * 0.3)

            data.append({
                "日期": date.strftime("%Y-%m-%d"),
                "活动ID": "ACT_2024_001",
                "活动分组名称": group,
                "营销人数": marketing_count,
                "余额": round(balance, 2),
                "收益": round(revenue, 2),
                "个人中心来访人数": visit_count,
                "借款人数": loan_count,
            })

    df = pd.DataFrame(data)
    return df


def test_create_test_file():
    """测试 1：创建测试数据文件"""
    print("\n" + "=" * 60)
    print("测试 1：创建 AB Test 测试数据")
    print("=" * 60)

    df = create_test_data()
    print(f"\n生成的测试数据：")
    print(df.to_string(index=False))

    # 保存到临时文件
    test_file = Path(tempfile.gettempdir()) / "ab_test_data.xlsx"
    df.to_excel(test_file, index=False)
    print(f"\n测试数据已保存到: {test_file}")

    return test_file


def test_session_and_import():
    """测试 2：会话管理和文件导入"""
    print("\n" + "=" * 60)
    print("测试 2：会话管理和文件导入")
    print("=" * 60)

    from data_agent.session import SessionManager

    # 创建会话
    session = SessionManager()
    print(f"\n会话 ID: {session.session_id}")
    print(f"导入目录: {session.import_dir}")
    print(f"导出目录: {session.export_dir}")
    print(f"Dagster 目录: {session.dagster_jobs_dir}")

    # 验证目录已创建
    assert session.import_dir.exists(), "导入目录未创建"
    assert session.export_dir.exists(), "导出目录未创建"
    assert session.dagster_jobs_dir.exists(), "Dagster 目录未创建"
    print("✓ 所有目录已正确创建")

    return session


def test_copy_file_to_imports(session, source_file):
    """测试 3：复制文件到 imports 目录"""
    print("\n" + "=" * 60)
    print("测试 3：复制文件到 imports 目录")
    print("=" * 60)

    import shutil

    dest_file = session.import_dir / "ab_test_data.xlsx"
    shutil.copy(source_file, dest_file)

    print(f"文件已复制到: {dest_file}")

    # 验证文件列表
    imports = session.list_imports()
    print(f"导入目录文件列表: {[f.name for f in imports]}")
    assert len(imports) == 1, "文件数量不正确"
    assert imports[0].name == "ab_test_data.xlsx", "文件名不正确"
    print("✓ 文件已正确导入")

    return dest_file


def test_list_preset_ops():
    """测试 4：列出预设操作"""
    print("\n" + "=" * 60)
    print("测试 4：列出预设操作")
    print("=" * 60)

    from data_agent.tools.dagster_tools import list_preset_ops

    result = list_preset_ops.invoke({})

    print(f"\n总操作数: {result['total_ops']}")
    print(f"类别: {result['categories']}")

    print("\n预设操作列表：")
    for category, ops in result['ops_by_category'].items():
        print(f"\n  [{category}]")
        for op in ops:
            print(f"    - {op['name']}: {op['description']}")

    assert result['total_ops'] > 10, "预设操作数量不足"
    assert "python_transform" in [op['name'] for ops in result['ops_by_category'].values() for op in ops]
    print("\n✓ 预设操作列表正确")

    return result


def test_list_import_files(session):
    """测试 5：列出导入文件"""
    print("\n" + "=" * 60)
    print("测试 5：列出导入文件")
    print("=" * 60)

    from data_agent.tools.dagster_tools import list_import_files

    result = list_import_files.invoke({"session_id": session.session_id})

    print(f"\n会话 ID: {result['session_id']}")
    print(f"导入目录: {result['import_dir']}")
    print(f"文件数量: {result['total']}")

    for f in result['files']:
        print(f"  - {f['name']} ({f['type']}, {f['size']} bytes)")

    assert result['total'] == 1, "文件数量不正确"
    assert result['files'][0]['name'] == "ab_test_data.xlsx"
    print("\n✓ 导入文件列表正确")

    return result


def test_generate_dag_code(session):
    """测试 6：生成 DAG 代码"""
    print("\n" + "=" * 60)
    print("测试 6：生成 DAG 代码（AB Test 效果指标计算）")
    print("=" * 60)

    from data_agent.tools.dagster_tools import generate_dag_code

    # 定义 AB Test 处理操作
    operations = [
        {
            "op": "python_transform",
            "comment": "计算 AB Test 效果指标",
            "params": {
                "code": '''
# AB Test 效果指标计算
import pandas as pd

# 1. 按分组汇总
grouped = df.groupby('活动分组名称').agg({
    '营销人数': 'first',
    '余额': 'sum',
    '收益': 'sum',
    '个人中心来访人数': 'sum',
    '借款人数': 'sum'
}).reset_index()

# 2. 计算拉平倍率（以最大营销人数组为基准）
base_count = grouped['营销人数'].max()
grouped['拉平倍率'] = base_count / grouped['营销人数']

# 3. 计算拉平后的值
grouped['余额_拉平'] = grouped['余额'] * grouped['拉平倍率']
grouped['收益_拉平'] = grouped['收益'] * grouped['拉平倍率']

# 4. 获取对照组数据
control_row = grouped[grouped['活动分组名称'] == '对照组'].iloc[0]
control_balance = control_row['余额_拉平']
control_revenue = control_row['收益_拉平']

# 5. 计算净增和倍率
grouped['余额净增'] = grouped['余额_拉平'] - control_balance
grouped['收益净增'] = grouped['收益_拉平'] - control_revenue
grouped['余额倍率'] = grouped['余额_拉平'] / control_balance
grouped['收益倍率'] = grouped['收益_拉平'] / control_revenue

# 6. 计算转化率
grouped['个人中心来访率'] = grouped['个人中心来访人数'] / grouped['营销人数']
grouped['借款率'] = grouped['借款人数'] / grouped['营销人数']

# 7. 格式化输出
result = grouped.round(4)
'''
            }
        }
    ]

    result = generate_dag_code.invoke({
        "description": "AB Test 效果指标计算：计算三组（6折满额券、15天满额券、对照组）的拉平倍率、净增、倍率和转化率",
        "input_files": ["ab_test_data.xlsx"],
        "output_file": "ab_test_效果指标.xlsx",
        "operations": operations,
        "session_id": session.session_id,
    })

    print(f"\n生成结果:")
    print(f"  作业 ID: {result['job_id']}")
    print(f"  作业文件: {result['job_file']}")
    print(f"  输入文件: {result['input_files']}")
    print(f"  输出文件: {result['output_file']}")
    print(f"  操作数量: {result['operations_count']}")

    print(f"\n操作描述:")
    for desc in result['operations_description']:
        print(f"  {desc}")

    print(f"\n代码预览 (前 1000 字符):")
    print("-" * 40)
    print(result['code_preview'][:1000])
    print("-" * 40)

    assert result['success'], "代码生成失败"
    assert Path(result['job_file']).exists(), "作业文件未创建"
    print("\n✓ DAG 代码生成成功")

    return result


def test_execute_dag_job(session, job_result):
    """测试 7：执行 DAG 作业"""
    print("\n" + "=" * 60)
    print("测试 7：执行 DAG 作业")
    print("=" * 60)

    from data_agent.tools.dagster_tools import execute_dag_job

    result = execute_dag_job.invoke({
        "job_id": job_result['job_id'],
        "session_id": session.session_id,
    })

    print(f"\n执行结果:")
    print(f"  成功: {result['success']}")
    print(f"  作业 ID: {result['job_id']}")

    if result['success']:
        print(f"\n输出:")
        print(result['output'])
    else:
        print(f"\n错误:")
        print(result.get('error', 'Unknown error'))

    assert result['success'], f"作业执行失败: {result.get('error')}"
    print("\n✓ DAG 作业执行成功")

    return result


def test_verify_output(session):
    """测试 8：验证输出文件"""
    print("\n" + "=" * 60)
    print("测试 8：验证输出文件")
    print("=" * 60)

    output_file = session.export_dir / "ab_test_效果指标.xlsx"

    assert output_file.exists(), f"输出文件不存在: {output_file}"
    print(f"输出文件: {output_file}")

    # 读取并显示结果
    df = pd.read_excel(output_file)
    print(f"\n输出数据 ({len(df)} 行, {len(df.columns)} 列):")
    print(df.to_string(index=False))

    # 验证计算结果
    assert '拉平倍率' in df.columns, "缺少拉平倍率列"
    assert '余额净增' in df.columns, "缺少余额净增列"
    assert '余额倍率' in df.columns, "缺少余额倍率列"
    assert '个人中心来访率' in df.columns, "缺少转化率列"

    # 验证对照组净增为 0
    control_row = df[df['活动分组名称'] == '对照组'].iloc[0]
    assert abs(control_row['余额净增']) < 0.01, "对照组余额净增应为 0"
    assert abs(control_row['余额倍率'] - 1.0) < 0.01, "对照组余额倍率应为 1"

    print("\n✓ 输出文件验证成功")
    print("\n效果指标汇总:")
    for _, row in df.iterrows():
        print(f"\n  [{row['活动分组名称']}]")
        print(f"    拉平倍率: {row['拉平倍率']:.4f}")
        print(f"    余额净增: {row['余额净增']:.2f}")
        print(f"    余额倍率: {row['余额倍率']:.4f}")
        print(f"    来访率: {row['个人中心来访率']:.2%}")
        print(f"    借款率: {row['借款率']:.2%}")

    return df


def test_list_dag_jobs(session):
    """测试 9：列出 DAG 作业"""
    print("\n" + "=" * 60)
    print("测试 9：列出 DAG 作业")
    print("=" * 60)

    from data_agent.tools.dagster_tools import list_dag_jobs

    result = list_dag_jobs.invoke({"session_id": session.session_id})

    print(f"\n作业目录: {result['jobs_dir']}")
    print(f"作业数量: {result['total']}")

    for job in result['jobs']:
        print(f"\n  作业 ID: {job['job_id']}")
        print(f"    描述: {job['description']}")
        print(f"    创建时间: {job['created']}")

    assert result['total'] >= 1, "应至少有一个作业"
    print("\n✓ 作业列表正确")

    return result


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Dagster 数据处理功能 - 端到端测试")
    print("场景：AB Test 效果指标计算")
    print("=" * 60)

    try:
        # 测试 1: 创建测试数据
        test_file = test_create_test_file()

        # 测试 2: 会话管理
        session = test_session_and_import()

        # 测试 3: 复制文件到 imports
        test_copy_file_to_imports(session, test_file)

        # 测试 4: 列出预设操作
        test_list_preset_ops()

        # 测试 5: 列出导入文件
        test_list_import_files(session)

        # 测试 6: 生成 DAG 代码
        job_result = test_generate_dag_code(session)

        # 测试 7: 执行 DAG 作业
        test_execute_dag_job(session, job_result)

        # 测试 8: 验证输出
        test_verify_output(session)

        # 测试 9: 列出作业
        test_list_dag_jobs(session)

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)

        # 返回会话信息供后续使用
        return {
            "session_id": session.session_id,
            "import_dir": str(session.import_dir),
            "export_dir": str(session.export_dir),
        }

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    run_all_tests()
