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

## 交互示例

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

## 技术栈

- **框架**: LangChain、DeepAgents、LangGraph
- **LLM**: OpenAI 兼容接口
- **数据分析**: pandas、numpy、scipy
- **机器学习**: scikit-learn
- **图分析**: networkx
- **数据库**: SQLAlchemy (支持MySQL、PostgreSQL)
- **CLI**: rich

## INFO
### 数据库配置
DB_CONNECTION=mysql+pymysql://fish:32KjyZ_uW9L9_Q5@rm-cn-v3m4jkbul00025to.rwlb.rds.aliyuncs.com:3306/fish

### AI API配置
API_KEY=a2d9aad92f254c17b3c71495177cc94b.vXbdUFVOvhGZnqf8
BASE_URL=https://open.bigmodel.cn/api/paas/v4
MODEL=glm-4.7