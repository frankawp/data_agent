# 数据开发Agent

基于LangGraph和DeepAgents框架开发的智能数据分析Agent，支持多轮交互、自动生成DAG执行计划，并能调用SQL、Python、pandas、scikit-learn、networkx等数据分析工具。

## 功能特性

- **多轮交互对话**：通过自然语言与Agent对话，明确数据分析需求
- **自动DAG生成**：Agent理解需求后，自动生成有向无环图（DAG）执行计划
- **可视化展示**：以Mermaid格式展示执行计划，用户确认后执行
- **丰富的工具集**：
  - **SQL工具**：支持MySQL、PostgreSQL数据库查询，DuckDB高性能分析
  - **Python执行**：MicroSandbox安全沙箱执行环境
  - **数据分析**：pandas、numpy、scipy数据处理和统计分析
  - **机器学习**：scikit-learn分类、回归、聚类
  - **图分析**：networkx图算法和网络分析
- **命令行界面**：基于rich库的美观CLI界面

## 技术栈

- **框架**: LangChain、LangGraph
- **LLM**: 智谱AI GLM-4.7
- **数据分析**: pandas、numpy、scipy、DuckDB
- **机器学习**: scikit-learn
- **图分析**: networkx
- **数据库**: SQLAlchemy (MySQL、PostgreSQL)
- **沙箱**: MicroSandbox
- **CLI**: rich

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository_url>
cd data_agent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

### 2. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入您的配置
# API_KEY=你的智谱AI API密钥
# DB_CONNECTION=你的数据库连接字符串
```

### 3. 可选：安装MicroSandbox

```bash
# macOS/Linux
curl -sSL https://get.microsandbox.dev | sh
msb server start
msb pull microsandbox/python
```

### 4. 启动Agent

```bash
# 方式1：使用命令行
data-agent

# 方式2：使用Python模块
python -m data_agent
```

## 使用示例

```
# 启动后，直接描述你的需求
您: 我需要分析用户表的注册趋势

Agent: 好的，我来帮您分析用户注册趋势。首先，我需要了解一些信息：
1. 用户表在哪里？数据库还是文件？
2. 您想分析什么时间范围的注册趋势？
3. 需要什么样的可视化输出？

您: 用户表在MySQL数据库中，我想分析最近6个月的月度注册量

Agent: 明白了。我将为您生成一个执行计划...

[DAG执行计划显示]

是否执行此计划？ (y/n): y

[执行中...]

执行结果:
✓ 查询用户数据: 成功
✓ 数据分析: 成功
✓ 生成趋势图: 成功

✓ 所有任务执行完成！
```

## 项目结构

```
data_agent/
├── pyproject.toml              # 项目配置
├── requirements.txt            # 依赖列表
├── Sandboxfile                 # MicroSandbox配置
├── .env.example                # 环境变量模板
├── src/
│   └── data_agent/
│       ├── main.py             # CLI入口
│       ├── config/             # 配置管理
│       ├── agent/              # Agent核心
│       ├── dag/                # DAG系统
│       ├── sandbox/            # 沙箱管理
│       ├── tools/              # 工具集
│       └── state/              # 状态管理
└── tests/                      # 测试
```

## 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| API_KEY | 智谱AI API密钥 | 必填 |
| BASE_URL | API基础URL | https://open.bigmodel.cn/api/paas/v4/ |
| MODEL | 模型名称 | glm-4.7 |
| DB_CONNECTION | 数据库连接字符串 | 必填 |
| SANDBOX_ENABLED | 是否启用沙箱 | true |
| DUCKDB_MEMORY_LIMIT | DuckDB内存限制 | 4GB |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/
ruff check src/
```

## 许可证

MIT License
