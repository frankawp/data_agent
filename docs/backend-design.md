# Data Agent 后端设计文档

## 1. 概述

Data Agent 是一个基于 DeepAgents + LangChain + LangGraph 框架构建的智能数据分析助手。后端采用混合架构设计，支持 CLI 同步交互和 FastAPI 异步 Web 服务两种模式。

### 1.1 技术栈

| 组件 | 技术选型 |
|------|---------|
| Web 框架 | FastAPI |
| 智能体框架 | DeepAgents + LangChain + LangGraph |
| LLM | 智谱 AI GLM-4 系列 (兼容 OpenAI API) |
| 数据分析 | pandas, scipy |
| 机器学习 | scikit-learn |
| 图分析 | networkx |
| 沙箱执行 | MicroSandbox |
| 可观测性 | LangSmith |

### 1.2 代码规模

- **总代码量**: ~5,980 行 Python 代码
- **核心模块**: 8 个主要模块
- **工具集**: 5 个工具包，10+ 个工具函数

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户交互层                                  │
├─────────────────┬─────────────────────┬─────────────────────────────┤
│   CLI 终端      │    FastAPI Web      │    CopilotKit 前端          │
│  (sync_cli.py)  │    (api/main.py)    │    (copilot.py)             │
└────────┬────────┴──────────┬──────────┴──────────────┬──────────────┘
         │                   │                          │
         └───────────────────┼──────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         核心智能体层                                  │
├─────────────────────────────────────────────────────────────────────┤
│  DataAgent (deep_agent.py)                                          │
│  ├── create_data_agent() 工厂函数                                    │
│  ├── chat() / stream() 对话接口                                      │
│  ├── ModeManager 模式管理                                            │
│  └── ConversationCompactor 对话压缩                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐
│   工具集层       │   │   会话管理层     │   │   执行环境层             │
├─────────────────┤   ├─────────────────┤   ├─────────────────────────┤
│ • sql_tools     │   │ SessionManager  │   │ MicroSandbox 远程沙箱   │
│ • python_tools  │   │ • 会话隔离       │   │ • 硬件隔离执行           │
│ • ml_tools      │   │ • 自动清理       │   │ • 超时控制              │
│ • graph_tools   │   │ • 导出管理       │   │ • 本地执行备选           │
│ • data_tools    │   │                 │   │                         │
└─────────────────┘   └─────────────────┘   └─────────────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           配置管理层                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Settings (settings.py) - 环境变量配置                               │
│  Modes (modes.py) - 运行模式管理                                     │
│  LLM (llm.py) - 大语言模型封装                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
src/data_agent/
├── __init__.py
├── main.py                      # CLI 主入口 (~150 行)
├── api/                         # Web API 模块
│   ├── __init__.py
│   ├── main.py                  # FastAPI 应用入口 (~60 行)
│   ├── chat.py                  # 聊天 API (~115 行)
│   ├── copilot.py               # CopilotKit 集成 (~256 行)
│   └── routes/                  # 路由模块
│       ├── __init__.py
│       ├── modes.py             # 模式管理路由 (~60 行)
│       ├── database.py          # 数据库路由 (~120 行)
│       └── sessions.py          # 会话路由 (~150 行)
├── agent/                       # 智能体核心
│   ├── __init__.py
│   ├── deep_agent.py            # DataAgent 核心 (~550 行)
│   ├── llm.py                   # LLM 封装 (~207 行)
│   ├── plan_executor.py         # 计划执行器 (~200 行)
│   └── compactor.py             # 对话压缩器 (~100 行)
├── tools/                       # 工具集
│   ├── __init__.py              # 工具导出
│   ├── sql_tools.py             # SQL 工具 (~300 行)
│   ├── python_tools.py          # Python 执行工具 (~200 行)
│   ├── ml_tools.py              # 机器学习工具 (~400 行)
│   ├── graph_tools.py           # 图分析工具 (~200 行)
│   └── data_tools.py            # 数据分析工具 (~150 行)
├── config/                      # 配置
│   ├── __init__.py
│   ├── settings.py              # 配置管理 (~167 行)
│   ├── modes.py                 # 模式管理 (~318 行)
│   └── prompts.py               # 系统提示模板
├── session/                     # 会话管理
│   ├── __init__.py
│   └── manager.py               # 会话管理器 (~232 行)
├── sandbox/                     # 沙箱执行
│   ├── __init__.py
│   └── microsandbox.py          # MicroSandbox 封装 (~250 行)
├── cli/                         # CLI 界面
│   ├── __init__.py
│   └── sync_cli.py              # 同步 CLI (~200 行)
└── ui/                          # UI 格式化
    ├── __init__.py
    └── formatter.py             # 输出格式化
```

---

## 3. 核心模块详解

### 3.1 DataAgent (智能体核心)

**文件**: `agent/deep_agent.py`

DataAgent 是整个系统的核心，负责管理对话、调用工具、执行任务。

#### 3.1.1 主要类和函数

```python
class DataAgent:
    """数据分析智能代理"""

    def __init__(self, graph, config, checkpointer=None):
        self.graph = graph              # LangGraph 图
        self.config = config            # 运行配置
        self.checkpointer = checkpointer
        self._conversation_history = [] # 对话历史

    def chat(self, message: str) -> str:
        """同步对话接口"""

    def stream(self, message: str):
        """流式对话接口，返回迭代器"""

    def reset(self):
        """重置对话历史"""

    def compress_history_if_needed(self):
        """当 token 超过阈值时压缩对话历史"""


def create_data_agent(
    session_id: str = None,
    db_connection: str = None,
    enable_plan_mode: bool = False
) -> DataAgent:
    """工厂函数：创建 DataAgent 实例"""
```

#### 3.1.2 对话流程

```
用户输入
    │
    ▼
┌───────────────────┐
│ 检查 token 是否   │
│ 超过阈值 (80%)    │
└─────────┬─────────┘
          │ 是
          ▼
┌───────────────────┐
│ ConversationCompactor │
│ 压缩历史对话        │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 构建消息列表       │
│ [系统提示, 历史,   │
│  当前消息]         │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ LangGraph 执行     │
│ • 调用 LLM        │
│ • 执行工具调用     │
│ • 迭代直到完成     │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 更新对话历史       │
│ 返回响应          │
└───────────────────┘
```

#### 3.1.3 流式输出回调

```python
# stream() 方法支持 4 种回调
def stream(
    self,
    message: str,
    on_token: Callable[[str], None] = None,      # LLM 输出 token
    on_tool_start: Callable[[str, dict], None] = None,  # 工具开始
    on_tool_end: Callable[[str, Any], None] = None,     # 工具结束
    on_error: Callable[[Exception], None] = None        # 错误处理
):
```

### 3.2 工具集 (Tools)

工具是 Agent 执行具体任务的能力扩展，使用 LangChain 的 `@tool` 装饰器定义。

#### 3.2.1 SQL 工具 (`sql_tools.py`)

```python
@tool
def execute_sql(query: str) -> str:
    """执行 SQL 查询（仅支持 SELECT）"""
    # 安全检查：黑名单关键字
    BLACKLIST = ['DROP', 'DELETE', 'UPDATE', 'INSERT',
                 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']

@tool
def list_tables() -> str:
    """列出数据库中所有表"""

@tool
def describe_table(table_name: str) -> str:
    """获取表结构信息"""
```

**安全机制**:
- 仅允许 SELECT 查询
- 黑名单过滤危险关键字
- 参数化查询防止 SQL 注入

#### 3.2.2 Python 执行工具 (`python_tools.py`)

```python
@tool
def execute_python_safe(code: str) -> str:
    """在沙箱中安全执行 Python 代码"""
    # 优先使用 MicroSandbox
    # 失败时回退到本地受限执行
```

**执行流程**:
```
代码输入
    │
    ▼
┌───────────────────┐
│ MicroSandbox 可用? │
└─────────┬─────────┘
    是    │    否
    ▼     │    ▼
┌─────────┴─────────┐
│ 远程沙箱执行       │  本地受限执行
│ • 完全隔离         │  • 白名单函数
│ • 超时控制         │  • 禁用危险模块
│ • 资源限制         │
└───────────────────┘
```

#### 3.2.3 机器学习工具 (`ml_tools.py`)

```python
# 支持的模型类型
ML_MODELS = {
    # 分类
    'logistic_regression': LogisticRegression,
    'random_forest_classifier': RandomForestClassifier,
    'gradient_boosting_classifier': GradientBoostingClassifier,
    'svm_classifier': SVC,
    'knn_classifier': KNeighborsClassifier,
    'decision_tree_classifier': DecisionTreeClassifier,
    'naive_bayes': GaussianNB,
    'mlp_classifier': MLPClassifier,

    # 回归
    'linear_regression': LinearRegression,
    'ridge_regression': Ridge,
    'lasso_regression': Lasso,
    'random_forest_regressor': RandomForestRegressor,
    'gradient_boosting_regressor': GradientBoostingRegressor,
    'svm_regressor': SVR,
    'decision_tree_regressor': DecisionTreeRegressor,
    'mlp_regressor': MLPRegressor,

    # 聚类
    'kmeans': KMeans,
    'dbscan': DBSCAN,
}

@tool
def train_model(
    model_type: str,
    data: str,           # JSON 格式数据
    target_column: str,
    model_name: str = None,
    **kwargs
) -> str:
    """训练机器学习模型"""

@tool
def predict(model_name: str, data: str) -> str:
    """使用已训练模型进行预测"""

@tool
def list_models() -> str:
    """列出所有已训练的模型"""

# 模型存储
_model_store: Dict[str, Any] = {}
```

#### 3.2.4 图分析工具 (`graph_tools.py`)

```python
@tool
def create_graph(
    edges: str,          # JSON 格式边列表
    graph_name: str = None,
    directed: bool = False
) -> str:
    """创建图"""

@tool
def graph_analysis(
    graph_name: str,
    analysis_type: str   # 'centrality', 'community', 'path', 'stats'
) -> str:
    """图分析"""

@tool
def list_graphs() -> str:
    """列出所有图"""

# 图存储
_graph_store: Dict[str, nx.Graph] = {}
```

#### 3.2.5 数据分析工具 (`data_tools.py`)

```python
@tool
def analyze_dataframe(
    data: str,           # JSON/CSV 格式数据
    operation: str       # 'describe', 'corr', 'groupby', 'pivot', etc.
) -> str:
    """对 DataFrame 进行分析操作"""
```

### 3.3 会话管理 (Session Manager)

**文件**: `session/manager.py`

```python
class SessionManager:
    """会话管理器 - 单例模式"""

    _instance = None

    def __init__(self, base_dir: str = "~/.data_agent/sessions"):
        self.base_dir = Path(base_dir).expanduser()
        self._sessions: Dict[str, SessionInfo] = {}
        self._lock = threading.Lock()

    def create_session(self, session_id: str = None) -> str:
        """创建新会话，返回 session_id"""

    def get_session_dir(self, session_id: str) -> Path:
        """获取会话目录"""

    def cleanup_old_sessions(self, max_age_days: int = 7):
        """清理过期会话"""

    def export_conversation(self, session_id: str, format: str = 'json'):
        """导出对话记录"""


@dataclass
class SessionInfo:
    session_id: str
    created_at: datetime
    last_active: datetime
    session_dir: Path
    exports: List[str]
```

**会话目录结构**:
```
~/.data_agent/sessions/
├── session_abc123/
│   ├── conversation.json    # 对话历史
│   ├── exports/             # 导出文件
│   │   ├── report_001.pdf
│   │   └── data_001.csv
│   └── models/              # 训练的模型
│       └── model_rf.pkl
└── session_def456/
    └── ...
```

### 3.4 模式管理 (Mode Manager)

**文件**: `config/modes.py`

```python
class ModeManager:
    """模式管理器 - 单例模式"""

    _instance = None

    # 支持的模式
    MODES = {
        'plan': Mode(
            key='plan',
            name='计划模式',
            description='执行前先生成任务计划',
            default=False
        ),
        'auto': Mode(
            key='auto',
            name='自动模式',
            description='自动执行无需确认',
            default=True
        ),
        'safe': Mode(
            key='safe',
            name='安全模式',
            description='限制危险操作',
            default=True
        ),
        'verbose': Mode(
            key='verbose',
            name='详细模式',
            description='显示详细执行信息',
            default=False
        ),
        'preview': Mode(
            key='preview',
            name='预览模式',
            description='只显示计划不执行',
            default=False
        ),
        'export': Mode(
            key='export',
            name='导出模式',
            description='自动导出结果',
            default=False
        ),
    }

    def get(self, mode_key: str) -> bool:
        """获取模式状态"""

    def set(self, mode_key: str, value: bool):
        """设置模式状态"""

    def toggle(self, mode_key: str) -> bool:
        """切换模式状态"""

    def save(self):
        """持久化保存到 ~/.data_agent/modes.json"""
```

### 3.5 沙箱执行 (MicroSandbox)

**文件**: `sandbox/microsandbox.py`

```python
class MicroSandboxExecutor:
    """MicroSandbox 代码执行器"""

    def __init__(
        self,
        sandbox_name: str = "data_agent",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self._sandbox = None
        self._connected = False

    async def connect(self):
        """连接到沙箱"""

    async def execute(self, code: str) -> ExecutionResult:
        """执行代码"""

    async def disconnect(self):
        """断开连接"""


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str = None
    execution_time: float = 0.0
```

**沙箱配置** (`Sandboxfile`):
```yaml
name: data_agent
image: python:3.11-slim
packages:
  - pandas
  - numpy
  - scipy
  - scikit-learn
  - networkx
  - matplotlib
timeout: 30
memory: 512M
```

### 3.6 LLM 封装 (llm.py)

**文件**: `agent/llm.py`

```python
def create_llm(
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    streaming: bool = False
) -> ChatOpenAI:
    """创建 LLM 实例

    支持所有 OpenAI 兼容的 API:
    - 智谱 AI (默认)
    - OpenAI
    - Azure OpenAI
    - 本地模型 (如 Ollama)
    """

    return ChatOpenAI(
        model=model or settings.MODEL_NAME,
        api_key=settings.API_KEY,
        base_url=settings.API_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
    )
```

**配置**:
```python
# settings.py
MODEL_NAME = os.getenv("MODEL_NAME", "glm-4")
API_KEY = os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
```

---

## 4. Web API 设计

### 4.1 FastAPI 应用结构

**文件**: `api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Data Agent API",
    description="智能数据分析助手 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(modes_router, prefix="/api/modes", tags=["modes"])
app.include_router(database_router, prefix="/api/database", tags=["database"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
```

### 4.2 API 端点

#### 4.2.1 聊天 API (`/api/chat`)

```python
# POST /api/chat
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: Optional[List[ToolCall]] = None

@router.post("/")
async def chat(request: ChatRequest) -> ChatResponse:
    """发送消息并获取回复"""

# POST /api/chat/reset
@router.post("/reset")
async def reset_chat(session_id: str):
    """重置会话"""

# GET /api/chat/sessions
@router.get("/sessions")
async def list_sessions() -> List[SessionInfo]:
    """列出所有会话"""
```

#### 4.2.2 模式 API (`/api/modes`)

```python
# GET /api/modes
@router.get("/")
async def get_all_modes() -> Dict[str, ModeInfo]:
    """获取所有模式状态"""

# POST /api/modes/{mode_key}
@router.post("/{mode_key}")
async def set_mode(mode_key: str, value: bool):
    """设置模式值"""

# POST /api/modes/{mode_key}/toggle
@router.post("/{mode_key}/toggle")
async def toggle_mode(mode_key: str) -> bool:
    """切换模式状态"""
```

#### 4.2.3 数据库 API (`/api/database`)

```python
# GET /api/database/tables
@router.get("/tables")
async def list_tables() -> List[str]:
    """获取所有表名"""

# GET /api/database/tables/{table_name}
@router.get("/tables/{table_name}")
async def describe_table(table_name: str) -> TableSchema:
    """获取表结构"""
```

#### 4.2.4 会话 API (`/api/sessions`)

```python
# GET /api/sessions
@router.get("/")
async def get_current_session() -> SessionInfo:
    """获取当前会话信息"""

# POST /api/sessions/new
@router.post("/new")
async def create_session() -> SessionInfo:
    """创建新会话"""

# GET /api/sessions/exports
@router.get("/exports")
async def list_exports(session_id: str) -> List[ExportFile]:
    """获取导出文件列表"""
```

### 4.3 CopilotKit 集成

**文件**: `api/copilot.py`

```python
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitSDK, Action

# CopilotKit 动作定义
actions = [
    Action(
        name="analyze_data",
        description="分析数据并生成报告",
        handler=analyze_data_handler,
        parameters=[
            {"name": "query", "type": "string", "description": "分析请求"}
        ]
    ),
    Action(
        name="execute_sql",
        description="执行 SQL 查询",
        handler=execute_sql_handler,
        parameters=[
            {"name": "sql", "type": "string", "description": "SQL 查询"}
        ]
    ),
    # ...更多动作
]

sdk = CopilotKitSDK(actions=actions)
add_fastapi_endpoint(app, sdk, "/copilot")
```

---

## 5. 数据流

### 5.1 聊天请求处理流程

```
客户端请求
    │
    ▼
┌─────────────────────────────────────────┐
│ FastAPI 路由 (/api/chat)                │
│ • 验证请求                               │
│ • 获取/创建会话                          │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ DataAgent.chat() / stream()             │
│ • 构建消息上下文                          │
│ • 检查并压缩历史                          │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ LangGraph 执行引擎                       │
│ • 调用 LLM 生成响应                       │
│ • 解析工具调用请求                        │
└────────┬─────────────────┬──────────────┘
         │                 │
    无工具调用          有工具调用
         │                 │
         │                 ▼
         │   ┌─────────────────────────────┐
         │   │ 工具执行层                   │
         │   │ • SQL: 查询数据库            │
         │   │ • Python: 沙箱执行           │
         │   │ • ML: 模型训练/预测          │
         │   │ • Graph: 图分析             │
         │   └─────────────┬───────────────┘
         │                 │
         │                 ▼
         │   ┌─────────────────────────────┐
         │   │ 工具结果返回 LLM             │
         │   │ • 生成自然语言响应            │
         │   └─────────────┬───────────────┘
         │                 │
         └────────┬────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 更新对话历史                             │
│ • 保存用户消息                           │
│ • 保存助手响应                           │
│ • 保存工具调用记录                        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 返回响应                                 │
│ • 同步: 完整响应                         │
│ • 流式: SSE 事件流                       │
└─────────────────────────────────────────┘
```

### 5.2 代码执行流程 (沙箱)

```
execute_python_safe(code)
    │
    ▼
┌─────────────────────────────────────────┐
│ 检查 MicroSandbox 连接状态               │
└─────────────────┬───────────────────────┘
         │                 │
      已连接            未连接
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│ 远程沙箱执行     │  │ 尝试连接沙箱    │
│ • 发送代码       │  │                │
│ • 等待结果       │  │                │
│ • 超时控制       │  └────────┬────────┘
└────────┬────────┘           │
         │              连接失败
         │                 │
         │                 ▼
         │         ┌─────────────────┐
         │         │ 本地受限执行     │
         │         │ • 白名单函数     │
         │         │ • 禁用危险模块   │
         │         │ • 超时控制       │
         │         └────────┬────────┘
         │                  │
         └────────┬─────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 返回执行结果                             │
│ • success: bool                         │
│ • output: str                           │
│ • error: str (如果失败)                  │
│ • execution_time: float                 │
└─────────────────────────────────────────┘
```

---

## 6. 安全设计

### 6.1 SQL 安全

```python
# sql_tools.py
DANGEROUS_KEYWORDS = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
    'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE', 'EXEC',
    'EXECUTE', 'xp_', 'sp_', '--', '/*', '*/', ';--'
]

def validate_sql(query: str) -> bool:
    """验证 SQL 查询安全性"""
    query_upper = query.upper()

    # 只允许 SELECT
    if not query_upper.strip().startswith('SELECT'):
        return False

    # 检查危险关键字
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in query_upper:
            return False

    return True
```

### 6.2 代码执行安全

```python
# 本地执行白名单
ALLOWED_BUILTINS = {
    'abs', 'all', 'any', 'bool', 'dict', 'enumerate',
    'filter', 'float', 'int', 'len', 'list', 'map',
    'max', 'min', 'print', 'range', 'round', 'set',
    'sorted', 'str', 'sum', 'tuple', 'zip',
}

ALLOWED_MODULES = {
    'math', 'statistics', 'collections', 'itertools',
    'functools', 'operator', 'json', 're', 'datetime',
    'pandas', 'numpy', 'scipy', 'sklearn',
}

FORBIDDEN_MODULES = {
    'os', 'sys', 'subprocess', 'shutil', 'socket',
    'urllib', 'requests', 'http', 'ftplib', 'smtplib',
    'pickle', 'shelve', 'marshal', 'importlib',
    '__builtins__', 'builtins', 'eval', 'exec', 'compile',
}
```

### 6.3 沙箱隔离

- **网络隔离**: 沙箱无法访问外部网络
- **文件系统隔离**: 只能访问临时目录
- **资源限制**: 内存、CPU、执行时间限制
- **进程隔离**: 无法生成子进程

---

## 7. 配置管理

### 7.1 环境变量

```bash
# .env 文件

# LLM 配置 (必需)
API_KEY=your_zhipu_api_key
MODEL_NAME=glm-4                    # 默认模型
API_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# 数据库配置 (可选)
DB_CONNECTION=mysql://user:pass@host:3306/db

# 沙箱配置 (可选)
MICROSANDBOX_ENABLED=true
MICROSANDBOX_HOST=localhost
MICROSANDBOX_PORT=8080
MICROSANDBOX_TIMEOUT=30

# LangSmith 可观测性 (可选)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=data-agent

# 日志级别
LOG_LEVEL=INFO
```

### 7.2 Settings 类

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    api_key: str
    model_name: str = "glm-4"
    api_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"

    # 数据库
    db_connection: Optional[str] = None

    # 沙箱
    microsandbox_enabled: bool = True
    microsandbox_host: str = "localhost"
    microsandbox_port: int = 8080
    microsandbox_timeout: int = 30

    # 会话
    session_base_dir: str = "~/.data_agent/sessions"
    session_max_age_days: int = 7

    # 对话
    max_history_tokens: int = 8000
    compression_threshold: float = 0.8

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 8. 部署

### 8.1 开发环境

```bash
# 安装依赖
pip install -e ".[dev]"

# 启动开发服务器
uvicorn data_agent.api.main:app --reload --port 8000

# 或使用 CLI
python -m data_agent
```

### 8.2 生产环境

```bash
# 使用 Gunicorn + Uvicorn workers
gunicorn data_agent.api.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000

# 或使用 Docker
docker build -t data-agent .
docker run -p 8000:8000 --env-file .env data-agent
```

### 8.3 Docker 配置

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "data_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 9. 扩展性设计

### 9.1 添加新工具

```python
# 1. 创建工具文件 tools/new_tools.py
from langchain.tools import tool

@tool
def my_new_tool(param1: str, param2: int) -> str:
    """工具描述 - LLM 会根据这个描述决定何时使用该工具

    Args:
        param1: 参数1说明
        param2: 参数2说明

    Returns:
        执行结果
    """
    # 实现逻辑
    return result

# 2. 在 tools/__init__.py 中导出
from .new_tools import my_new_tool

__all__ = [
    # ... 现有工具
    "my_new_tool",
]

# 3. 工具会自动被 DataAgent 加载使用
```

### 9.2 添加新 API 路由

```python
# 1. 创建路由文件 api/routes/new_routes.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/endpoint")
async def my_endpoint():
    return {"result": "data"}

# 2. 在 api/main.py 中注册
from .routes.new_routes import router as new_router

app.include_router(new_router, prefix="/api/new", tags=["new"])
```

### 9.3 支持新的 LLM 提供商

```python
# 只需修改环境变量即可支持任何 OpenAI 兼容的 API
API_BASE_URL=https://api.openai.com/v1/        # OpenAI
API_BASE_URL=https://api.deepseek.com/v1/      # DeepSeek
API_BASE_URL=http://localhost:11434/v1/        # Ollama
```

---

## 10. 常见使用场景

### 10.1 数据分析

```
用户: 分析 sales 表的销售趋势

Agent 执行流程:
1. list_tables() -> 获取表列表
2. describe_table('sales') -> 获取表结构
3. execute_sql('SELECT date, SUM(amount) FROM sales GROUP BY date ORDER BY date') -> 查询数据
4. execute_python_safe('...matplotlib绑图代码...') -> 生成图表
5. 返回分析结果和可视化
```

### 10.2 机器学习

```
用户: 用销售数据训练一个预测模型

Agent 执行流程:
1. execute_sql('SELECT * FROM sales') -> 获取数据
2. analyze_dataframe(data, 'describe') -> 数据探索
3. execute_python_safe('...数据预处理代码...') -> 特征工程
4. train_model('random_forest_regressor', data, 'sales_amount') -> 训练模型
5. 返回模型性能指标
```

### 10.3 图分析

```
用户: 分析用户之间的关系网络

Agent 执行流程:
1. execute_sql('SELECT user1, user2, interaction FROM user_relations') -> 获取关系数据
2. create_graph(edges, 'user_network') -> 创建图
3. graph_analysis('user_network', 'centrality') -> 中心性分析
4. graph_analysis('user_network', 'community') -> 社区发现
5. 返回分析结果
```

---

## 11. 附录

### 11.1 错误码

| 错误码 | 说明 |
|-------|------|
| 400 | 请求参数错误 |
| 401 | API Key 无效 |
| 403 | 操作被拒绝 (安全限制) |
| 404 | 资源不存在 |
| 408 | 执行超时 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 503 | 沙箱服务不可用 |

### 11.2 依赖列表

```toml
[project.dependencies]
# Web 框架
fastapi = ">=0.100.0"
uvicorn = ">=0.22.0"

# 智能体框架
langchain = ">=0.2.0"
langgraph = ">=0.1.0"
langchain-openai = ">=0.1.0"

# 数据处理
pandas = ">=2.0.0"
numpy = ">=1.24.0"
scipy = ">=1.10.0"

# 机器学习
scikit-learn = ">=1.3.0"

# 图分析
networkx = ">=3.0"

# 沙箱
microsandbox = ">=0.1.0"

# 工具
pydantic = ">=2.0.0"
pydantic-settings = ">=2.0.0"
python-dotenv = ">=1.0.0"
rich = ">=13.0.0"
```

### 11.3 参考链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [智谱 AI API](https://open.bigmodel.cn/)
- [MicroSandbox](https://github.com/anthropics/microsandbox)
