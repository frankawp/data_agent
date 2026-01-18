# Data Agent

基于 DeepAgents 框架的智能数据分析 Agent，支持自然语言交互、自动任务规划、SQL 查询、数据分析、机器学习和图分析。

## 功能特性

### 核心能力

- **自然语言交互**: 使用中文或英文描述你的数据分析需求
- **SQL 查询**: 支持 MySQL、PostgreSQL、DuckDB，自动生成和执行 SQL
- **数据分析**: 基于 pandas、numpy、scipy 的数据处理和统计分析
- **机器学习**: 集成 scikit-learn，支持 15+ 种模型（分类、回归、聚类）
- **图分析**: 使用 networkx 进行社交网络、知识图谱等图结构分析

### 安全特性

- **SQL 安全**: 仅支持 SELECT 查询，内置关键字黑名单防护
- **沙箱执行**: 使用 MicroSandbox 隔离执行 Python 代码
- **会话隔离**: 每个会话拥有独立的沙箱和导出目录

## 架构

### 多代理协作架构

```
CLI (main.py) / Web (web/) / API (api/main.py)
                    ↓
            DataAgent (Coordinator)
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
data-collector  data-analyzer  report-writer
(SQL 查询)     (Python 分析)   (图表生成)
    ↓               ↓               ↓
list_tables    execute_python   execute_python
describe_table train_model      export_dataframe
execute_sql    graph_analysis   export_text
                    ↓
        沙箱 (MicroSandbox 隔离执行)
```

### 子代理职责

| 子代理 | 职责 | 主要工具 |
|--------|------|----------|
| **data-collector** | 数据采集、SQL 查询、表结构探索 | `list_tables`, `describe_table`, `execute_sql` |
| **data-analyzer** | 统计分析、机器学习建模、图分析 | `execute_python_safe`, `train_model`, `graph_analysis` |
| **report-writer** | 可视化图表、分析报告生成 | `execute_python_safe`, `export_dataframe` |

### 工具集

```
工具集 (tools/)
├── sql_tools.py      # SQL 查询（仅 SELECT，有黑名单防护）
├── data_tools.py     # pandas/scipy 数据分析
├── ml_tools.py       # scikit-learn 机器学习（15+ 模型）
├── graph_tools.py    # networkx 图分析
└── python_tools.py   # 安全 Python 执行
```

### 支持的机器学习模型

| 类型 | 模型 |
|------|------|
| 分类 | LogisticRegression, DecisionTree, RandomForest, SVC, KNN, NaiveBayes |
| 回归 | LinearRegression, Ridge, Lasso, DecisionTree, RandomForest, SVR, KNN |
| 聚类 | KMeans, DBSCAN |

## 安装

### 前置要求

- Python >= 3.10
- 智谱 AI API Key

### 基础安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/data-agent.git
cd data-agent

# 安装
pip install -e .
```

### 开发模式安装

```bash
pip install -e ".[dev]"
```

## 配置

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

### 必需配置

```bash
# 智谱 AI 配置
API_KEY=your_zhipu_api_key_here
BASE_URL=https://open.bigmodel.cn/api/paas/v4/
MODEL=glm-4.7
```

### 可选配置

```bash
# 数据库配置
DB_CONNECTION=mysql+pymysql://user:password@host:port/database

# MicroSandbox 配置
SANDBOX_ENABLED=true
SANDBOX_SERVER_URL=http://localhost:8080
SANDBOX_TIMEOUT=30
SANDBOX_MEMORY=2048

# DuckDB 配置
DUCKDB_MEMORY_LIMIT=4GB
DUCKDB_THREADS=4

# Agent 配置
MAX_ITERATIONS=10
CONVERSATION_MEMORY_SIZE=20

# 日志配置
LOG_LEVEL=INFO
```

### Agent 系统配置

除了环境变量，还可以通过 `agents.yaml` 文件配置多代理系统。配置文件按以下顺序查找：

1. `~/.data_agent/agents.yaml` （用户自定义）
2. `./config/agents.yaml` （项目目录）
3. 内置默认配置

#### 配置示例

```yaml
# agents.yaml
version: "1.0"

# LLM 配置
llm:
  default:
    model: ${MODEL:deepseek-chat}
    api_key: ${API_KEY}
    temperature: 0.7
  profiles:
    fast:
      model: ${MODEL:deepseek-chat}
      temperature: 0.5

# 工具开关
tools:
  builtin:
    sql_tools: true
    python_tools: true
    ml_tools: true
    graph_tools: true

# 子代理配置
subagents:
  data-collector:
    description: "从数据库采集数据"
    llm: fast
    tools:
      - list_tables
      - describe_table
      - execute_sql
    prompt_file: prompts/data_collector.md

  data-analyzer:
    description: "分析数据并提取洞察"
    llm: default
    tools:
      - execute_python_safe
      - train_model
    prompt_file: prompts/data_analyzer.md
```

详细配置说明请参考 [配置指南](docs/configuration.md)。

## 使用方法

### CLI 模式

```bash
# 直接运行
data-agent

# 或使用模块方式
python -m data_agent
```

### API 模式

```bash
# 启动 API 服务器
data-agent-api

# 或指定端口
uvicorn data_agent.api.main:app --host 0.0.0.0 --port 8000
```

### CLI 命令

在 CLI 交互模式下，支持以下斜杠命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/config` | 查看当前 Agent 配置 |
| `/reload` | 重新加载配置文件 |
| `/modes` | 查看运行时模式状态 |
| `/plan on\|off\|auto` | 切换计划模式 |
| `/auto on\|off` | 切换自动执行模式 |
| `/safe on\|off` | 切换安全模式 |
| `/preview 10\|50\|100\|all` | 设置数据预览行数 |
| `/clear` | 清除对话历史 |

### 示例对话

```
> 列出数据库中的所有表
> 查看 users 表的结构
> 查询最近7天注册的用户数量
> 对用户数据进行聚类分析，找出不同用户群体
> 训练一个随机森林模型预测用户流失
```

## Docker 部署

### 构建镜像

```bash
docker build -t data-agent .
```

### 运行容器

```bash
docker run -p 8000:8000 \
  -e API_KEY=your_api_key \
  -e DB_CONNECTION=your_db_connection \
  data-agent
```

### Railway 部署

项目已配置 Dockerfile，可直接部署到 Railway。环境变量通过 Railway 控制台配置。

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/test_deepagent.py -v

# 端到端测试（需要数据库）
pytest tests/test_mysql_e2e.py -v
```

### 代码质量

```bash
# 格式化
black src/

# 代码检查
ruff check src/

# 自动修复
ruff check src/ --fix
```

### 添加新工具

1. 在 `tools/` 目录创建新文件
2. 使用 `@tool` 装饰器定义工具函数
3. 编写完整的 docstring（LLM 依赖它理解工具用途）
4. 在 `tools/__init__.py` 中导出

## 许可证

MIT
