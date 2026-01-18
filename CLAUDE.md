# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

数据开发Agent - 基于 DeepAgents 框架构建的智能数据分析助手，支持自然语言交互、自动任务规划、SQL查询、数据分析、机器学习和图分析。

## 常用命令

```bash
# 运行应用
./run.sh                    # 推荐方式，自动激活虚拟环境
data-agent                  # 安装后直接运行
python -m data_agent        # 模块方式运行

# 安装
pip install -e .            # 开发模式安装
pip install -e ".[dev]"     # 包含开发依赖

# 测试
pytest                                      # 运行所有测试
pytest tests/test_deepagent.py -v          # 运行单元测试
pytest tests/test_mysql_e2e.py -v          # 端到端测试（需要数据库）
pytest tests/test_deepagent.py::TestDataAgentCreation -v  # 运行单个测试类

# 代码质量
black src/                  # 格式化
ruff check src/             # 检查
ruff check src/ --fix       # 自动修复
```

## 架构

### 多 Agent 系统

```
用户输入
    ↓
DataAgent (agent/deep_agent.py)
    ↓
协调者 Agent (multi_agent.py)
    ├── data-collector   # SQL 查询、表结构探索
    ├── data-analyzer    # 统计分析、ML、图分析
    └── report-writer    # 可视化、报告生成
    ↓
工具集 (tools/)
    ↓
MicroSandbox 沙箱隔离
```

### 配置化架构

Agent 系统支持通过 YAML 配置文件定义子代理、工具、LLM：

- **配置文件**: `config/agents.yaml` 或 `~/.data_agent/agents.yaml`
- **提示词文件**: `config/prompts/*.md`
- **配置加载器**: `config/loader.py` - 支持环境变量替换 `${VAR:default}`
- **工具注册表**: `tools/registry.py` - 按名称获取工具，支持别名和禁用
- **子代理工厂**: `agent/factory.py` - 根据配置动态创建子代理
- **热重载**: `config/watcher.py` - 监听配置文件变化

无配置文件时自动回退到 `agent/subagents/` 中的硬编码默认配置。

### 关键文件

| 文件 | 职责 |
|------|------|
| `main.py` | CLI 主入口，输出格式化，流式显示 |
| `agent/deep_agent.py` | DataAgent 类，对话历史管理，Plan Mode |
| `agent/multi_agent.py` | 多 Agent 协调，使用 DeepAgents 框架 |
| `agent/factory.py` | 子代理工厂，从配置创建子代理 |
| `config/settings.py` | Pydantic 环境变量配置 |
| `config/schema.py` | Agent 配置 Schema（LLM Profile、子代理等） |
| `config/loader.py` | YAML 配置加载，环境变量替换 |
| `tools/registry.py` | 工具注册表，按名称获取工具 |

### 工具设计模式

- 工具使用 LangChain `@tool` 装饰器
- ML 模型存储在 `_model_store` 字典中
- 图存储在 `_graph_store` 字典中
- SQL 工具有安全防护：仅 SELECT，黑名单过滤危险关键字

### 工具注册表 (tools/registry.py)

工具注册表管理所有可用工具：

```python
from data_agent.tools.registry import get_tool_registry

registry = get_tool_registry()

# 按名称获取工具
tool = registry.get("execute_sql")

# 获取所有工具
all_tools = registry.list_tools()

# 按别名获取
tool = registry.get("db_query")  # 别名 -> execute_sql

# 禁用/启用工具
registry.disable("execute_sql")
registry.enable("execute_sql")
```

**内置工具组** (15 个工具)：
- `sql_tools`: list_tables, describe_table, execute_sql
- `python_tools`: execute_python_safe, list_variables, clear_variables, export_dataframe, export_text, list_exports, glob, read_file, ls
- `ml_tools`: train_model, predict, list_models
- `graph_tools`: create_graph, graph_analysis, list_graphs

### 会话管理

- `session/manager.py` 管理会话隔离
- 每个会话拥有独立的导出目录 `~/.data_agent/sessions/{session_id}/exports/`
- Python 变量在会话中持久化

## 配置

### 环境变量（.env 文件）

```bash
API_KEY=your_api_key           # 必需
BASE_URL=https://api.deepseek.com
MODEL=deepseek-chat
DB_CONNECTION=mysql+pymysql://user:pass@host:port/db  # 可选
SANDBOX_ENABLED=true           # MicroSandbox 沙箱
```

### Agent 配置 (agents.yaml)

```yaml
llm:
  default:
    model: ${MODEL:deepseek-chat}
    temperature: 0.7
  profiles:
    fast: { model: deepseek-chat, temperature: 0.5 }

subagents:
  my-agent:
    description: "代理描述"
    llm: fast
    tools: [tool1, tool2]
    prompt_file: prompts/my_agent.md
```

### CLI 命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/config` | 查看当前 Agent 配置（LLM、子代理、工具） |
| `/reload` | 重新加载配置文件（不影响当前会话） |
| `/modes` | 查看运行时模式状态 |
| `/plan on\|off\|auto` | 切换计划模式 |
| `/auto on\|off` | 切换自动执行模式 |
| `/safe on\|off` | 切换安全模式（危险 SQL 操作保护） |
| `/preview 10\|50\|100\|all` | 设置数据预览行数 |
| `/export on\|off` | 切换自动导出模式 |
| `/clear` | 清除对话历史 |

### 配置文件位置优先级

1. `~/.data_agent/agents.yaml` （用户自定义，优先）
2. `src/data_agent/config/agents.yaml` （项目内置）
3. 内置默认配置（无配置文件时回退）

## 注意事项

- 跟我使用中文交流，写注释和说明文档都是中文
- 添加新工具时在 `tools/` 目录创建，并在 `tools/__init__.py` 导出
- 工具函数需要完整的 docstring，因为 LLM 依赖它理解工具用途
- 调用涉及到网络的命令（pip、msb 等）需要先 `unset HTTPS_PROXY` 去掉代理
- 启动 MicroSandbox 前需要先取消代理设置：`unset HTTPS_PROXY && msb run data_agent`
