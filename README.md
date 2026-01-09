# 数据开发Agent

基于LangChain DeepAgents框架开发的智能数据分析Agent，支持多轮交互、自动生成DAG执行计划，并能调用SQL、Python、pandas、scikit-learn、networkx等数据分析工具。

## 功能特性

- **多轮交互对话**：通过自然语言与Agent对话，明确数据分析需求
- **自动DAG生成**：Agent理解需求后，自动生成有向无环图（DAG）执行计划
- **可视化展示**：以Mermaid格式展示执行计划，用户确认后执行
- **丰富的工具集**：
  - **SQL工具**：支持MySQL、PostgreSQL数据库查询
  - **Python执行**：安全的Python代码执行环境
  - **数据分析**：pandas、numpy、scipy数据处理和统计分析
  - **机器学习**：scikit-learn分类、回归、聚类
  - **图分析**：networkx图算法和网络分析
- **命令行界面**：基于rich库的美观CLI界面

## 安装

### 1. 克隆项目

```bash
cd /Users/frankliu/Code/data_agent
```

### 2. 激活虚拟环境

```bash
source .venv/bin/activate
```

### 3. 安装依赖

依赖已经在项目初始化时安装完成。如果需要重新安装：

```bash
pip install -r requirements.txt
```

## 配置

### API密钥

需要设置Anthropic API密钥：

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

或者在运行时通过参数指定：

```bash
python -m data_agent.main --api-key your-api-key-here
```

### 数据库连接（可选）

如果要使用数据库功能，可以通过参数指定数据库连接：

```bash
python -m data_agent.main --db "mysql+pymysql://user:password@localhost:3306/database"
```

支持的数据库格式：
- MySQL: `mysql+pymysql://user:password@host:port/database`
- PostgreSQL: `postgresql+psycopg2://user:password@host:port/database`

## 使用方法

### 启动Agent

```bash
python -m data_agent.main
```

或者使用安装的命令行工具（如果已安装）：

```bash
data-agent
```

### 交互示例

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

### 命令列表

- `exit` / `quit`: 退出程序
- `help`: 显示帮助信息
- `clear`: 清空屏幕
- `status`: 查看当前状态

## 项目结构

```
data_agent/
├── src/data_agent/
│   ├── main.py                      # CLI入口
│   ├── agent/
│   │   ├── core.py                  # 核心Agent逻辑
│   │   └── executor.py              # DAG执行器
│   ├── tools/
│   │   ├── sql_tools.py             # SQL工具
│   │   ├── python_tools.py          # Python执行工具
│   │   ├── data_tools.py            # 数据分析工具
│   │   ├── ml_tools.py              # 机器学习工具
│   │   └── graph_tools.py           # 图分析工具
│   ├── dag/
│   │   ├── models.py                # DAG数据模型
│   │   ├── generator.py             # DAG生成器
│   │   └── visualizer.py            # DAG可视化
│   ├── state/
│   │   └── graph_state.py           # 状态定义
│   └── config/
│       └── settings.py              # 配置管理
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 技术栈

- **框架**: LangChain、DeepAgents、LangGraph
- **LLM**: Anthropic Claude (Sonnet 4.5)
- **数据分析**: pandas、numpy、scipy
- **机器学习**: scikit-learn
- **图分析**: networkx
- **数据库**: SQLAlchemy (支持MySQL、PostgreSQL)
- **CLI**: rich

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
ruff check src/
```

## 注意事项

1. **安全性**：Python代码执行在隔离环境中进行，但仍需注意不要执行不受信任的代码
2. **数据库**：SQL查询使用SQLAlchemy参数化，防止SQL注入
3. **资源限制**：大数据集处理时注意内存使用

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 作者

Your Name <your.email@example.com>
