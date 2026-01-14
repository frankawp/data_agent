# 数据分析智能平台技术架构文档

## 一、平台概述

### 1.1 定位

一个利用 AI 协助业务完成数据分析的智能平台，支持：
- 自然语言交互式数据分析
- 从 Hive 数据仓库到 OLAP 加速层的数据加工 Pipeline
- 业务人员自助分析，产出 SQL 逻辑、分析模型、可视化报告
- **百GB级数据分析能力**

### 1.2 核心能力

| 能力域 | 描述 |
|--------|------|
| **智能分析** | 基于 DeepAgents 的多 Agent 协作，自然语言驱动 |
| **数据 Pipeline** | Hive → OLAP加速层 数据同步和加工 |
| **本体模型** | 保持与 Hive 表结构一致，统一数据语义 |
| **安全沙箱** | MicroSandbox 隔离执行，保障数据安全 |
| **大数据分析** | 基于 OLAP 引擎，支持百GB级数据秒级响应 |

---

## 二、整体技术架构

### 2.1 分层架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户接入层                                      │
├───────────────┬─────────────────────┬───────────────────────────────────┤
│   CLI 终端     │    Web 前端          │    API 网关                        │
│  (sync_cli)   │  (Next.js + React)  │    (认证/限流)                     │
└───────────────┴─────────────────────┴───────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       应用服务层 (FastAPI)                                │
├─────────────────────────────────────────────────────────────────────────┤
│  Chat API  │  Pipeline API  │  Ontology API  │  Modes API  │ Session API │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐
│   智能体核心层     │  │   Pipeline 引擎   │  │     本体模型层             │
├───────────────────┤  ├───────────────────┤  ├───────────────────────────┤
│ DataAgent         │  │ PipelineExecutor  │  │ OntologyManager           │
│ ├─ data-collector │  │ ├─ DAGScheduler   │  │ ├─ TableMapping           │
│ ├─ data-analyzer  │  │ ├─ StatusTracker  │  │ ├─ ColumnMapping          │
│ ├─ report-writer  │  │ └─ RollbackHandler│  │ └─ SchemaValidator        │
│ └─ pipeline-agent │  └───────────────────┘  └───────────────────────────┘
└───────────────────┘           │                        │
        │                       │                        │
        └───────────────────────┼────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            工具执行层                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ SQL Tools │ Python Tools │ ML Tools │ Graph Tools │ Pipeline Tools      │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────────┐  ┌───────────────────────────┐  ┌───────────────────┐
│   Hive 数据层     │  │   OLAP 加速层              │  │   执行环境层       │
├───────────────────┤  ├───────────────────────────┤  ├───────────────────┤
│ HiveConnector     │  │ OLAPConnector             │  │ MicroSandbox      │
│ ├─ PyHive/Thrift  │  │ ├─ StarRocks/Doris        │  │ LocalExecutor     │
│ └─ Kerberos Auth  │  │ ├─ MySQL协议兼容          │  └───────────────────┘
└───────────────────┘  │ └─ 列式存储/向量化执行     │
        │              └───────────────────────────┘
        │                       │
        │   数据流向 ══════►    │
        └───────────────────────┘
```

### 2.2 核心设计原则

1. **分层解耦**：接入层、服务层、Agent层、工具层、数据层职责清晰
2. **增量扩展**：在现有架构基础上新增模块，复用已有能力
3. **本体驱动**：数据模型基于 Hive 表结构本体，保持一致性
4. **双源协同**：Hive（源数据）+ OLAP引擎（加速层）协同工作
5. **大数据就绪**：支持百GB至PB级数据分析，秒级响应

---

## 三、数据流设计

### 3.1 数据流向图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           数据源层 (Hive)                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │
│  │ ODS 层  │  │ DWD 层  │  │ DWS 层  │  │ ADS 层  │                      │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘                      │
│       └────────────┴────────────┴────────────┘                           │
│                             │                                             │
│              ┌──────────────┴──────────────┐                              │
│              │   Pipeline 数据抽取          │                              │
│              │ (全量/增量同步/CDC)          │                              │
│              └──────────────┬──────────────┘                              │
└─────────────────────────────┼────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    OLAP 加速层 (StarRocks/Doris)                          │
│                                                                           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐   │
│  │  原始表 (raw_)   │ ─► │  中间表 (mid_)   │ ─► │  结果表 (result_)    │   │
│  │  (Hive镜像)     │    │  (加工逻辑)      │    │  (分析就绪)         │   │
│  └─────────────────┘    └─────────────────┘    └─────────────────────┘   │
│           ▲                                              │                │
│           │           本体模型约束                        ▼                │
│           │         (字段映射/类型校验)        ┌─────────────────────┐    │
│           └────────────────────────────────── │   物化视图层         │    │
│                                               │  (预聚合加速)        │    │
│                                               └─────────────────────┘    │
│  特性: 列式存储 | 向量化执行 | MPP架构 | MySQL协议兼容                      │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        分析层 (Agent System)                              │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  业务人员自然语言请求                                               │   │
│  │  "分析过去30天的用户活跃度变化趋势，并预测下周数据"                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                              │                                            │
│                              ▼                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │ data-collector  │  │ data-analyzer   │  │    report-writer        │   │
│  │ (从OLAP查询)    │─►│ (统计/ML分析)   │─►│  (输出SQL/模型/报告)    │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘   │
│                                                                           │
│  产出: SQL逻辑 / 分析模型 / 可视化报告 / 预测结果                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据处理三阶段

| 阶段 | 描述 | 关键操作 |
|------|------|----------|
| **Phase 1: 抽取** | Hive → OLAP | 全量/增量同步，Routine Load 实时同步 |
| **Phase 2: 加工** | OLAP 内部 | JOIN/聚合/清洗，物化视图预计算 |
| **Phase 3: 分析** | Agent 驱动 | 自然语言查询，ML 建模，报告生成 |

---

## 四、Pipeline 模块设计

### 4.1 模块结构

```
src/data_agent/pipeline/
├── __init__.py
├── core/                        # 核心引擎
│   ├── executor.py              # Pipeline 执行器
│   ├── scheduler.py             # DAG 调度器
│   ├── step.py                  # 步骤定义
│   └── status.py                # 状态管理
├── connectors/                  # 数据连接器
│   ├── hive_connector.py        # Hive 连接器
│   └── olap_connector.py        # OLAP 连接器（StarRocks/Doris）
├── steps/                       # 步骤实现
│   ├── extract.py               # 数据抽取步骤
│   ├── transform.py             # 数据转换步骤
│   ├── load.py                  # 数据加载步骤
│   └── validate.py              # 数据验证步骤
├── templates/                   # Pipeline 模板
│   └── sync_hive_to_olap.yaml   # Hive同步模板
└── registry.py                  # Pipeline 注册表
```

### 4.2 Pipeline 配置示例

```yaml
id: sync_user_activity
name: 用户活动数据同步
description: 从 Hive 同步用户活动数据到 OLAP 加速层
schedule: "0 2 * * *"  # 每天凌晨2点

variables:
  partition_date: "${YESTERDAY}"
  batch_size: 10000

steps:
  - id: extract_user_activity
    name: 抽取用户活动数据
    type: extract
    config:
      source_table: dwd.dwd_user_activity_di
      target_table: raw_user_activity
      mode: incremental
      incremental_column: dt

  - id: transform_clean
    name: 数据清洗
    type: transform
    depends_on: [extract_user_activity]
    config:
      sql: |
        INSERT INTO mid_user_activity_clean
        SELECT user_id, action_type, action_time, dt
        FROM raw_user_activity
        WHERE dt = '${partition_date}'

  - id: aggregate_metrics
    name: 聚合用户指标
    type: transform
    depends_on: [transform_clean]
    config:
      sql: |
        INSERT INTO result_user_daily_metrics
        SELECT user_id, dt, COUNT(*) as action_count
        FROM mid_user_activity_clean
        GROUP BY user_id, dt

  - id: validate_result
    name: 验证结果数据
    type: validate
    depends_on: [aggregate_metrics]
    config:
      table: result_user_daily_metrics
      rules:
        - type: row_count
          min: 1000
        - type: null_check
          columns: [user_id, dt]
```

---

## 五、本体模型设计

### 5.1 设计理念

采用**本体模型**：OLAP 加速层的表结构与 Hive 源表保持一致，通过元数据管理实现：
- 字段名称映射
- 数据类型转换规则
- 业务语义注解

### 5.2 模块结构

```
src/data_agent/ontology/
├── __init__.py
├── core/
│   ├── manager.py               # 本体管理器
│   ├── table_entity.py          # 表实体定义
│   ├── column_entity.py         # 列实体定义
│   └── validator.py             # 验证器
├── sync/
│   ├── hive_scanner.py          # Hive 元数据扫描
│   └── olap_sync.py             # OLAP 结构同步
└── store/
    └── json_store.py            # JSON 文件存储
```

### 5.3 核心数据结构

```python
@dataclass
class TableEntity:
    id: str                      # 唯一标识
    name: str                    # 表名
    database: str                # 数据库
    source_type: DataSourceType  # hive/mysql

    # 结构信息
    columns: List[ColumnEntity]
    partition_columns: List[str]

    # 业务分类
    layer: str                   # ods/dwd/dws/ads
    domain: str                  # 业务域
    subject: str                 # 主题

    # 映射信息
    hive_table: Optional[str]    # 对应的 Hive 表
    olap_table: Optional[str]    # 对应的 OLAP 表

@dataclass
class ColumnEntity:
    name: str
    data_type: ColumnType
    original_type: str           # 原始数据库类型

    # 映射信息
    hive_name: Optional[str]
    olap_name: Optional[str]

    # 业务语义
    business_name: str           # 业务名称
    business_category: str       # 维度/指标/属性
```

---

## 六、Agent 集成设计

### 6.1 新增 PipelineAgent

```python
PIPELINE_AGENT_CONFIG = {
    "name": "pipeline-agent",
    "description": "管理数据加工 Pipeline。用于执行 Hive 到 OLAP 的数据同步、运行数据加工任务。",
    "tools": [
        list_pipelines,       # 列出 Pipeline
        run_pipeline,         # 执行 Pipeline
        sync_hive_table,      # 同步 Hive 表
        hive_query,           # Hive 查询
        olap_query,           # OLAP 查询
        get_ontology,         # 获取本体信息
    ],
}
```

### 6.2 新增工具

| 工具 | 功能 |
|------|------|
| `list_pipelines` | 列出所有已注册的 Pipeline |
| `run_pipeline` | 执行指定的 Pipeline |
| `sync_hive_table` | 同步 Hive 表到 OLAP 加速层 |
| `hive_query` | 在 Hive 上执行查询（只读） |
| `olap_query` | 在 OLAP 上执行分析查询 |
| `get_ontology` | 获取表的本体信息 |

### 6.3 增强现有工具

- `describe_table` 增加本体语义信息
- `execute_sql` 支持本体感知的列映射

---

## 七、技术选型

### 7.1 OLAP 加速层选型（核心）

针对 **百GB级数据分析** 需求，推荐以下 OLAP 引擎：

| 引擎 | 推荐场景 | 核心优势 | 劣势 |
|------|----------|----------|------|
| **StarRocks** (首选) | 实时数仓、多表JOIN、高并发 | 性能最强、向量化执行、智能物化视图、MySQL协议兼容 | 社区相对较新 |
| **Apache Doris** | 通用BI报表、易用性优先 | 开箱即用、社区活跃、生态丰富 | 多表JOIN性能略逊 |
| **ClickHouse** | 日志分析、单表聚合 | 单表查询极快、压缩比高 | 多表JOIN弱、扩缩容复杂 |

**选型建议：**
- **数据量 100GB-1TB，需要复杂分析** → **StarRocks**（多表JOIN性能比Doris快5-10倍）
- **追求易用性和社区支持** → **Apache Doris**
- **主要是日志类单表聚合** → **ClickHouse**

**StarRocks/Doris 优势：**
- ✅ 兼容 MySQL 协议，现有 SQL 工具可直接复用
- ✅ 列式存储 + 向量化执行，百GB数据秒级响应
- ✅ 支持物化视图，自动预聚合加速
- ✅ 支持实时数据更新（主键模型）
- ✅ MPP 架构，水平扩展能力强

### 7.2 其他组件选型

| 组件 | 推荐技术 | 选型理由 |
|------|----------|----------|
| **Hive 连接** | PyHive + Thrift | 成熟稳定，社区支持好 |
| **Hive 认证** | Kerberos | 企业级安全标准 |
| **OLAP 连接** | MySQL Connector（协议兼容） | StarRocks/Doris 兼容 MySQL 协议 |
| **Pipeline 引擎** | 自研轻量引擎 | 轻量集成，避免额外依赖 |
| **本体存储** | JSON → SQLite | 初期简单，后期可扩展 |
| **调度器** | APScheduler | 内嵌式，无需额外服务 |
| **数据验证** | Great Expectations | 成熟的数据质量框架 |

### 7.3 数据规模与响应时间参考

| 数据规模 | StarRocks/Doris 预期响应 | MySQL 预期响应 |
|----------|-------------------------|---------------|
| 10GB | 毫秒级 | 秒级 |
| 100GB | 秒级 | 分钟级 |
| 1TB | 秒-十秒级 | 不可用 |
| 10TB | 十秒级 | 不可用 |

---

## 八、配置扩展

```python
# config/settings.py 新增配置项

# Hive 配置
HIVE_HOST: str
HIVE_PORT: int = 10000
HIVE_DATABASE: str = "default"
HIVE_AUTH: str = "NONE"  # NONE/KERBEROS/LDAP

# OLAP 加速层配置 (StarRocks/Doris)
OLAP_TYPE: str = "starrocks"  # starrocks/doris/clickhouse
OLAP_HOST: str
OLAP_PORT: int = 9030         # StarRocks/Doris FE 查询端口
OLAP_HTTP_PORT: int = 8030    # StarRocks/Doris FE HTTP 端口
OLAP_DATABASE: str = "default"
OLAP_USERNAME: str = "root"
OLAP_PASSWORD: Optional[str] = None
OLAP_POOL_SIZE: int = 10

# Pipeline 配置
PIPELINE_REGISTRY_PATH: str = "~/.data_agent/pipelines"
PIPELINE_MAX_CONCURRENT: int = 3
PIPELINE_DEFAULT_TIMEOUT: int = 3600

# 本体配置
ONTOLOGY_STORE_PATH: str = "~/.data_agent/ontology"
ONTOLOGY_AUTO_SYNC: bool = True
```

---

## 九、API 扩展

### 9.1 Pipeline API

```
POST /api/pipelines                    # 创建 Pipeline
GET  /api/pipelines                    # 列出所有 Pipeline
GET  /api/pipelines/{id}               # 获取 Pipeline 详情
POST /api/pipelines/{id}/run           # 执行 Pipeline
GET  /api/pipelines/{id}/runs          # 获取执行历史
GET  /api/pipelines/runs/{run_id}      # 获取执行详情
```

### 9.2 Ontology API

```
GET  /api/ontology/tables              # 列出所有表本体
GET  /api/ontology/tables/{id}         # 获取表本体详情
POST /api/ontology/sync                # 从 Hive 同步本体
GET  /api/ontology/mappings            # 获取映射关系
```

---

## 十、实现路径

### Phase 1: 基础设施
- Hive 连接器开发
- Pipeline 核心框架
- 配置扩展

### Phase 2: 本体模型
- 本体核心模型
- Hive 元数据扫描
- 本体查询 API

### Phase 3: Pipeline 增强
- 步骤实现（Extract/Transform/Load/Validate）
- DAG 调度
- 模板和注册表

### Phase 4: Agent 集成
- PipelineAgent SubAgent
- 增强现有 SubAgent
- API 路由

### Phase 5: 完善优化
- 监控告警
- Web UI 支持
- 文档测试

---

## 十一、目录结构变更

```
src/data_agent/
├── agent/
│   └── subagents/
│       └── pipeline_agent.py        # 新增
├── tools/
│   ├── pipeline_tools.py            # 新增
│   ├── olap_tools.py                # 新增 (OLAP 查询工具)
│   └── ontology_tools.py            # 新增
├── pipeline/                         # 新增模块
│   ├── core/
│   ├── connectors/
│   │   ├── hive_connector.py
│   │   └── olap_connector.py        # StarRocks/Doris 连接器
│   ├── steps/
│   └── templates/
├── ontology/                         # 新增模块
│   ├── core/
│   ├── sync/
│   └── store/
└── api/routes/
    ├── pipelines.py                 # 新增
    └── ontology.py                  # 新增
```

---

## 十二、关键文件

| 文件路径 | 用途 |
|---------|------|
| `src/data_agent/agent/deep_agent.py` | DataAgent 核心，需集成 PipelineAgent |
| `src/data_agent/agent/multi_agent.py` | 多Agent协调器，注册新 SubAgent |
| `src/data_agent/tools/sql_tools.py` | SQL工具，增强本体感知，支持 OLAP 查询 |
| `src/data_agent/config/settings.py` | 配置管理，扩展 OLAP/Hive/Pipeline 配置 |
| `src/data_agent/api/main.py` | API入口，注册新路由 |

---

## 十三、参考资料

- [StarRocks vs ClickHouse 2025对比](https://segmentfault.com/a/1190000047117032)
- [四大OLAP数据库对比: Doris vs StarRocks vs ClickHouse vs TiDB](https://zhuanlan.zhihu.com/p/1956380477297501556)
- [ClickHouse vs StarRocks 选型对比](https://my.oschina.net/u/4021911/blog/5345019)
