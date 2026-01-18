# 配置指南

本文档详细说明 Data Agent 的配置系统，包括环境变量、YAML 配置文件、提示词管理等。

## 配置文件位置

配置文件按以下顺序查找（优先级从高到低）：

1. `~/.data_agent/agents.yaml` - 用户自定义配置
2. `src/data_agent/config/agents.yaml` - 项目内置配置
3. 内置默认值 - 无配置文件时的回退配置

> 建议将自定义配置放在 `~/.data_agent/agents.yaml`，这样不会被项目更新覆盖。

## 环境变量

环境变量通过 `.env` 文件配置，支持在 `agents.yaml` 中引用。

### 必需配置

```bash
API_KEY=your_api_key_here     # LLM API 密钥
```

### 可选配置

```bash
# LLM 配置
BASE_URL=https://api.deepseek.com    # API 基础 URL
MODEL=deepseek-chat                   # 模型名称

# 数据库配置
DB_CONNECTION=mysql+pymysql://user:password@host:port/database

# MicroSandbox 沙箱配置
SANDBOX_ENABLED=true                  # 是否启用沙箱
SANDBOX_SERVER_URL=http://localhost:8080
SANDBOX_TIMEOUT=30                    # 执行超时（秒）
SANDBOX_MEMORY=2048                   # 内存限制（MB）

# DuckDB 配置
DUCKDB_MEMORY_LIMIT=4GB
DUCKDB_THREADS=4

# Agent 配置
MAX_ITERATIONS=10                     # 最大迭代次数
CONVERSATION_MEMORY_SIZE=20           # 对话记忆大小

# 日志配置
LOG_LEVEL=INFO
```

## agents.yaml 配置详解

### 环境变量替换

配置文件支持环境变量替换语法：

```yaml
# 基本用法
api_key: ${API_KEY}

# 带默认值
model: ${MODEL:deepseek-chat}    # 如果 MODEL 未设置，使用 deepseek-chat
```

### 完整配置结构

```yaml
version: "1.0"

# LLM 配置
llm:
  default: { ... }      # 默认配置
  profiles: { ... }     # 命名配置

# 工具配置
tools:
  builtin: { ... }      # 内置工具开关
  aliases: { ... }      # 工具别名

# 子代理配置
subagents:
  agent-name: { ... }

# 协调者配置
coordinator: { ... }

# 热重载配置
hot_reload: { ... }
```

---

### LLM 配置

定义 LLM 模型参数，支持多个 Profile 供不同子代理使用。

```yaml
llm:
  # 默认配置（用于未指定 llm 的子代理）
  default:
    model: ${MODEL:deepseek-chat}
    base_url: ${BASE_URL:https://api.deepseek.com}
    api_key: ${API_KEY}
    temperature: 0.7
    max_tokens: 4096

  # 命名 Profile（供子代理引用）
  profiles:
    # 快速响应（低温度、短输出）
    fast:
      model: ${MODEL:deepseek-chat}
      temperature: 0.5
      max_tokens: 2048

    # 高质量输出（高温度、长输出）
    powerful:
      model: ${MODEL:deepseek-chat}
      temperature: 0.8
      max_tokens: 8192
```

#### LLM Profile 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | string | deepseek-chat | 模型名称 |
| `base_url` | string | - | API 基础 URL，空则使用全局配置 |
| `api_key` | string | - | API 密钥，空则使用全局配置 |
| `temperature` | float | 0.7 | 生成温度，范围 0-2 |
| `max_tokens` | int | - | 最大输出 token 数 |

---

### 工具配置

控制工具的启用、禁用和别名。

```yaml
tools:
  # 内置工具组开关
  builtin:
    sql_tools: true      # SQL 工具（list_tables, describe_table, execute_sql）
    python_tools: true   # Python 工具（execute_python_safe, export_dataframe 等）
    ml_tools: true       # 机器学习工具（train_model, predict 等）
    graph_tools: true    # 图分析工具（create_graph, graph_analysis 等）

  # 工具别名（可选）
  aliases:
    db_query: execute_sql           # db_query -> execute_sql
    run_python: execute_python_safe # run_python -> execute_python_safe
```

#### 内置工具清单

| 工具组 | 工具名称 | 说明 |
|--------|----------|------|
| **sql_tools** | `list_tables` | 列出数据库中的所有表 |
|  | `describe_table` | 描述表结构（字段、类型） |
|  | `execute_sql` | 执行 SQL 查询（仅 SELECT） |
| **python_tools** | `execute_python_safe` | 安全执行 Python 代码 |
|  | `list_variables` | 列出当前会话变量 |
|  | `clear_variables` | 清除会话变量 |
|  | `export_dataframe` | 导出 DataFrame 到文件 |
|  | `export_text` | 导出文本到文件 |
|  | `list_exports` | 列出已导出的文件 |
|  | `glob` | 文件路径模式匹配 |
|  | `read_file` | 读取文件内容 |
|  | `ls` | 列出目录内容 |
| **ml_tools** | `train_model` | 训练机器学习模型 |
|  | `predict` | 使用模型进行预测 |
|  | `list_models` | 列出已训练的模型 |
| **graph_tools** | `create_graph` | 创建图结构 |
|  | `graph_analysis` | 图分析（中心性、社区检测等） |
|  | `list_graphs` | 列出已创建的图 |

---

### 子代理配置

定义各子代理的职责、工具和 LLM。

```yaml
subagents:
  # 数据采集子代理
  data-collector:
    description: "从数据库采集数据。用于 SQL 查询、表结构探索、数据预览。"
    llm: fast                        # 引用 LLM profile
    tools:
      - list_tables
      - describe_table
      - execute_sql
    prompt_file: prompts/data_collector.md

  # 数据分析子代理
  data-analyzer:
    description: "分析数据并提取洞察。用于统计分析、机器学习建模、图分析。"
    llm: powerful
    tools:
      - execute_python_safe
      - train_model
      - predict
      - create_graph
      - graph_analysis
    prompt_file: prompts/data_analyzer.md

  # 报告生成子代理
  report-writer:
    description: "生成可视化图表和分析报告。"
    llm: default
    tools:
      - execute_python_safe
      - export_dataframe
      - export_text
    prompt_file: prompts/report_writer.md
```

#### 子代理参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `description` | string | ✅ | 子代理功能描述，协调者根据此分配任务 |
| `llm` | string | - | LLM profile 名称，默认 "default" |
| `tools` | list | - | 可用工具名称列表 |
| `prompt_file` | string | - | 外部提示词文件路径 |
| `system_prompt` | string | - | 内联系统提示词（优先级低于 prompt_file） |

---

### 协调者配置

协调者负责分析用户请求并将任务分配给合适的子代理。

```yaml
coordinator:
  llm: default                       # 使用的 LLM profile
  prompt_file: prompts/coordinator.md
  use_default_prompt: true           # 是否使用默认提示词
```

---

### 热重载配置

支持配置文件变化时自动重新加载（实验性功能）。

```yaml
hot_reload:
  enabled: false                     # 是否启用
  watch_paths:                       # 监听路径
    - config/agents.yaml
    - config/prompts/
  debounce_ms: 1000                  # 防抖延迟（毫秒）
```

---

## 提示词文件

提示词文件位于 `config/prompts/` 目录，使用 Markdown 格式。

### 目录结构

```
config/prompts/
├── coordinator.md      # 协调者提示词
├── data_collector.md   # 数据采集子代理提示词
├── data_analyzer.md    # 数据分析子代理提示词
└── report_writer.md    # 报告生成子代理提示词
```

### 提示词示例

```markdown
# data_collector.md

你是一个数据采集专家。你的职责是：

1. 探索数据库结构（表、字段、类型）
2. 编写高效的 SQL 查询
3. 确保查询安全（仅使用 SELECT）

## 可用工具

- `list_tables`: 列出所有表
- `describe_table`: 查看表结构
- `execute_sql`: 执行 SQL 查询

## 注意事项

- 大表查询请使用 LIMIT
- 返回原始数据，不做分析
```

---

## 配置示例

### 最小配置

```yaml
version: "1.0"

llm:
  default:
    api_key: ${API_KEY}
```

### 自定义子代理

添加一个新的子代理：

```yaml
subagents:
  # 保留默认子代理...

  # 新增：数据质量检查子代理
  data-quality:
    description: "检查数据质量。用于发现缺失值、异常值、数据一致性问题。"
    llm: fast
    tools:
      - execute_sql
      - execute_python_safe
    system_prompt: |
      你是一个数据质量专家。检查数据时关注：
      - 缺失值比例
      - 数据类型一致性
      - 异常值检测
```

### 使用不同的 LLM

```yaml
llm:
  default:
    model: gpt-4
    base_url: https://api.openai.com/v1
    api_key: ${OPENAI_API_KEY}
    temperature: 0.7

  profiles:
    claude:
      model: claude-3-opus
      base_url: https://api.anthropic.com
      api_key: ${ANTHROPIC_API_KEY}
```

---

## CLI 命令

在运行时可以通过 CLI 命令查看和管理配置：

| 命令 | 说明 |
|------|------|
| `/config` | 查看当前 Agent 配置（LLM、子代理、工具） |
| `/reload` | 重新加载配置文件（不影响当前会话） |
| `/modes` | 查看运行时模式状态 |

### /config 输出示例

```
📋 Agent 配置
════════════════════════════════════════

🤖 LLM 配置
  默认: deepseek-chat (temp=0.7)
  Profiles:
    - fast: deepseek-chat (temp=0.5)
    - powerful: deepseek-chat (temp=0.8)

👥 子代理 (3)
  data-collector:
    描述: 从数据库采集数据...
    LLM: fast
    工具: list_tables, describe_table, execute_sql

  data-analyzer:
    描述: 分析数据并提取洞察...
    LLM: powerful
    工具: execute_python_safe, train_model, ...

  report-writer:
    描述: 生成可视化图表和分析报告...
    LLM: default
    工具: execute_python_safe, export_dataframe, ...

🔧 工具配置
  内置工具组: sql_tools ✓, python_tools ✓, ml_tools ✓, graph_tools ✓
  别名: db_query -> execute_sql, run_python -> execute_python_safe
```

---

## 故障排除

### 配置文件未加载

1. 检查文件路径是否正确
2. 检查 YAML 语法是否有效
3. 使用 `/reload` 命令重新加载

### 环境变量未替换

1. 确保 `.env` 文件存在且格式正确
2. 检查变量名是否匹配（区分大小写）
3. 使用 `${VAR:default}` 提供默认值

### 工具不可用

1. 检查 `tools.builtin` 中对应工具组是否启用
2. 检查子代理配置中是否包含该工具
3. 使用 `/config` 查看当前工具配置
