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

```
CLI (main.py)
    ↓
DataAgent (agent/deep_agent.py)
    ↓ create_data_agent() 工厂函数
DeepAgents 图 + 智谱 AI LLM (glm-4.7)
    ↓
工具集 (tools/)
├── sql_tools.py      # SQL 查询（仅 SELECT，有黑名单防护）
├── data_tools.py     # pandas/scipy 数据分析
├── ml_tools.py       # scikit-learn 机器学习（15+ 模型）
├── graph_tools.py    # networkx 图分析
└── python_tools.py   # 安全 Python 执行
    ↓
沙箱 (sandbox/microsandbox.py) - MicroSandbox 隔离执行
```

## 关键文件

- `src/data_agent/main.py` - CLI 主程序，输出格式化，流式显示
- `src/data_agent/agent/deep_agent.py` - DataAgent 类，对话历史管理
- `src/data_agent/config/settings.py` - 环境变量配置（API_KEY、DB连接）
- `src/data_agent/config/prompts.py` - 系统提示模板
- `Sandboxfile` - MicroSandbox 配置

## 工具设计模式

- 工具使用 LangChain `@tool` 装饰器
- ML 模型存储在 `_model_store` 字典中
- 图存储在 `_graph_store` 字典中
- SQL 工具有安全防护：仅 SELECT，黑名单过滤危险关键字

## 配置

环境变量（.env 文件）：
- `API_KEY` - 智谱 AI API 密钥（必需）
- `DB_CONNECTION` - 数据库连接字符串（可选）
- `MICROSANDBOX_*` - 沙箱配置

## 注意事项

- 跟我使用中文交流，写注释和说明文档都是中文
- 添加新工具时在 `tools/` 目录创建，并在 `tools/__init__.py` 导出
- 工具函数需要完整的 docstring，因为 LLM 依赖它理解工具用途
- 启动 MicroSandbox 前需要先取消代理设置：`unset HTTPS_PROXY && msb run data_agent`
