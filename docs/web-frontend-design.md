# Data Agent Web 前端设计文档

## 概述

Data Agent Web 是基于 CopilotKit 构建的数据分析 Web 界面，为专业数据分析师提供比 CLI 更友好的交互体验。

### 设计原则

**复用现有 Python 逻辑，只升级界面** - 所有业务逻辑（DataAgent、工具集、模式管理、会话管理）保持不变，CopilotKit 仅作为 Web 前端层。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Next.js 前端 (UI 层)                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  CopilotKit React 组件                                        │   │
│  │  - CopilotSidebar (对话面板)                                  │   │
│  │  - Generative UI (工具结果渲染)                                │   │
│  │  - 模式切换控件 (复用 ModeManager)                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI 后端 (API 层)                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CopilotKit Python SDK                                         │ │
│  │  - add_fastapi_endpoint → 连接现有工具集                        │ │
│  │  - Actions → 包装 LangChain 工具                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                    │                                 │
│                                    ▼                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              现有 Python 逻辑 (100% 复用)                        │ │
│  │                                                                 │ │
│  │  DataAgent          ModeManager        SessionManager           │ │
│  │  - chat_stream()    - plan_mode        - session_id             │ │
│  │  - Plan Mode        - auto_execute     - export_dir             │ │
│  │  - 对话压缩          - safe_mode        - 会话隔离               │ │
│  │                     - verbose                                   │ │
│  │  Tools (工具集)                                                  │ │
│  │  - execute_sql, list_tables, describe_table                     │ │
│  │  - execute_python_safe (沙箱执行)                                │ │
│  │  - train_model, predict, list_models                            │ │
│  │  - create_graph, graph_analysis, list_graphs                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端框架** | Next.js 16 + React 19 | App Router 模式 |
| **样式** | Tailwind CSS 4 | 原子化 CSS |
| **AI 对话** | @copilotkit/react-core, @copilotkit/react-ui | CopilotSidebar 组件 |
| **类型检查** | TypeScript 5 | 严格模式 |
| **后端** | FastAPI + CopilotKit Python SDK | API 层 |
| **核心逻辑** | 现有 DataAgent + 工具集 | 100% 复用 |

## 项目结构

```
web/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── layout.tsx                # 根布局，CopilotKit Provider
│   │   ├── page.tsx                  # 主页面
│   │   ├── globals.css               # 全局样式
│   │   └── api/                      # API 路由（代理到 Python 后端）
│   │       ├── copilotkit/route.ts   # CopilotKit 代理
│   │       ├── modes/
│   │       │   ├── route.ts          # GET /api/modes
│   │       │   └── [mode]/route.ts   # GET/POST /api/modes/:mode
│   │       ├── database/
│   │       │   └── tables/
│   │       │       ├── route.ts      # GET /api/database/tables
│   │       │       └── [tableName]/route.ts
│   │       └── sessions/
│   │           ├── route.ts          # GET /api/sessions
│   │           └── exports/route.ts  # GET /api/sessions/exports
│   │
│   ├── components/                   # React 组件
│   │   ├── Header.tsx                # 顶部栏
│   │   ├── sidebar/
│   │   │   └── Sidebar.tsx           # 左侧边栏
│   │   ├── workspace/
│   │   │   ├── Workspace.tsx         # Tab 容器
│   │   │   ├── MainWorkspace.tsx     # 主工作区
│   │   │   └── SecondaryWorkspace.tsx # 副工作区
│   │   ├── modes/
│   │   │   └── ModeControl.tsx       # 模式控制面板
│   │   └── data-display/
│   │       ├── DataTable.tsx         # 数据表格
│   │       └── CodeViewer.tsx        # 代码高亮
│   │
│   └── hooks/                        # React Hooks
│       └── useWorkspaceContext.tsx   # 工作区状态管理
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.ts
```

## 界面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header: Logo | 会话 ID | 数据库状态 | [模式设置]                     │
├──────────────┬──────────────────────────────────┬───────────────────┤
│              │  [主工作区] [副工作区]  ← Tab 切换  │                   │
│   侧边栏      │ ─────────────────────────────────│   CopilotSidebar  │
│   (可点击)   │                                  │  (AI 与人类交流)   │
│              │  ┌────────────────────────────┐  │                   │
│  数据库浏览器 │  │  ┌──────────────────────┐  │  │  对话输入         │
│  → 表列表    │  │  │ [历史模式提示条]     │  │  │                   │
│              │  │  │ 正在查看步骤#2 [退出]│  │  │  ─────────────    │
│  已训练模型  │  │  └──────────────────────┘  │  │  执行计划确认     │
│  → 模型列表  │  │                            │  │  ┌─────────────┐  │
│              │  │     AI 操作内容展示        │  │  │ 目标: xxx   │  │
│  导出文件    │  │                            │  │  │ ✓ 步骤1     │  │
│  → 下载/预览 │  │  • SQL + 结果表格          │  │  │ → 步骤2     │  │
│              │  │  • Python + 输出/图表      │  │  │ ○ 步骤3     │  │
│              │  │  • 模型评估指标            │  │  │ [确认] [取消]│  │
│              │  │                            │  │  └─────────────┘  │
│              │  └────────────────────────────┘  │  (可点击已完成步骤)│
└──────────────┴──────────────────────────────────┴───────────────────┘
```

## 核心组件设计

### 1. 布局层级

```tsx
// app/layout.tsx - CopilotKit Provider 包装
<CopilotKit runtimeUrl="/api/copilotkit">
  {children}
</CopilotKit>

// app/page.tsx - 主页面结构
<WorkspaceProvider>
  <div className="flex h-screen flex-col">
    <Header />
    <div className="flex flex-1">
      <Sidebar />           {/* 左侧边栏 */}
      <Workspace />         {/* 主/副工作区 */}
      <CopilotSidebar />    {/* AI 对话面板 */}
    </div>
  </div>
</WorkspaceProvider>
```

### 2. 工作区状态管理

```typescript
// hooks/useWorkspaceContext.tsx

interface WorkspaceContextType {
  // Tab 状态
  activeTab: "main" | "secondary";
  setActiveTab: (tab: "main" | "secondary") => void;

  // 副工作区内容（侧边栏点击时设置）
  secondaryContent: SecondaryContent | null;
  setSecondaryContent: (content: SecondaryContent | null) => void;

  // 历史查看模式
  viewMode: "live" | "historical";
  historicalStep: HistoricalStep | null;
  showHistoricalStep: (step: HistoricalStep) => void;
  exitHistoricalView: () => void;

  // 当前工具执行结果
  currentToolResult: ToolResult | null;
  setCurrentToolResult: (result: ToolResult | null) => void;

  // 执行历史
  stepHistory: HistoricalStep[];
  addStepToHistory: (step: HistoricalStep) => void;
  clearHistory: () => void;
}
```

### 3. 主工作区 (MainWorkspace)

主工作区展示 AI 调用工具的**具体操作内容**：

| 工具调用 | 显示内容 |
|---------|---------|
| execute_sql | SQL 语句（高亮）+ 查询结果表格 |
| execute_python_safe | Python 代码 + 执行输出 / 图表 |
| train_model | 模型参数 + 训练结果 + 评估指标 |
| predict | 输入数据 + 预测结果 |
| describe_table | 表结构详情 |
| graph_analysis | 图可视化 + 分析结果 |

**历史查看功能**：用户在 CopilotSidebar 中点击已完成步骤时，主工作区切换显示该历史操作内容，并显示"退出历史查看"按钮。

### 4. 副工作区 (SecondaryWorkspace)

用于用户主动点击左侧边栏时查看详情：

| 侧边栏点击项 | 副工作区显示 |
|-------------|-------------|
| 表名 | 表结构详情 (字段、类型、索引) |
| 已训练模型 | 模型参数 + 评估指标 |
| 导出文件 | 文件预览 + 下载按钮 |
| 图对象 | 图可视化 + 节点/边统计 |

### 5. CopilotSidebar

负责 AI 与用户的**交流内容**：
- 对话消息
- 执行计划（Plan Mode）
- 步骤进度（可点击查看历史）
- 工具调用确认

## 模式支持

与 CLI 完全一致的模式控制：

| 模式 | CLI 命令 | Web 控件 | 说明 |
|------|----------|----------|------|
| plan_mode | `/plan off\|on\|auto` | 下拉选择 | off=直接执行, on=先规划后确认, auto=复杂任务自动规划 |
| auto_execute | `/auto on\|off` | 开关 | 是否自动执行工具调用 |
| safe_mode | `/safe on\|off` | 开关 | 限制危险 SQL 操作 |
| verbose | `/verbose on\|off` | 开关 | 显示详细思考过程 |
| preview_limit | `/preview 10\|50\|100\|all` | 下拉选择 | 数据预览行数 |
| export_mode | `/export on\|off` | 开关 | 自动保存结果到文件 |

## API 设计

### 前端 API 路由（代理到 Python 后端）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/copilotkit` | POST | CopilotKit 对话代理 |
| `/api/modes` | GET | 获取所有模式状态 |
| `/api/modes/:mode` | GET/POST | 获取/设置单个模式 |
| `/api/database/tables` | GET | 获取表列表 |
| `/api/database/tables/:tableName` | GET | 获取表结构 |
| `/api/sessions` | GET | 获取当前会话信息 |
| `/api/sessions/exports` | GET | 获取导出文件列表 |

### 后端 API（FastAPI）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/copilotkit` | POST | CopilotKit SDK 端点 |
| `/api/modes` | GET | 获取所有模式 |
| `/api/modes/:mode_key` | POST | 设置模式值 |
| `/api/database/tables` | GET | 列出所有表 |
| `/api/database/tables/:table_name` | GET | 获取表 Schema |
| `/api/sessions` | GET | 获取会话信息 |
| `/api/sessions/exports` | GET | 列出导出文件 |

## 数据流

### 对话流程

```
用户输入 → CopilotSidebar → /api/copilotkit → Python 后端
                                                    ↓
                                            CopilotKit SDK
                                                    ↓
                                            调用 Actions (工具)
                                                    ↓
                                            返回结果
                                                    ↓
CopilotSidebar ← 对话更新 ← /api/copilotkit ←───────┘
      ↓
MainWorkspace ← 工具执行结果展示
```

### 模式切换流程

```
用户点击模式设置 → ModeControl 组件
        ↓
    更新 UI 状态
        ↓
POST /api/modes/:mode → Python 后端
        ↓
    ModeManager.set()
        ↓
    返回新状态
        ↓
    更新 UI 确认
```

## 启动方式

### 开发环境

```bash
# 1. 启动后端 (端口 8000)
cd /path/to/data_agent
python -m data_agent.api.main

# 2. 启动前端 (端口 3000)
cd /path/to/data_agent/web
npm run dev

# 3. 访问
open http://localhost:3000
```

### 生产环境

```bash
# 构建前端
cd web
npm run build

# 启动前端
npm run start

# 后端使用 Gunicorn
gunicorn data_agent.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 环境变量

### 前端 (.env.local)

```env
BACKEND_URL=http://localhost:8000
```

### 后端 (.env)

```env
API_KEY=your_api_key
DB_CONNECTION=mysql://user:pass@host:port/db
```

## 扩展计划

### 阶段一（当前）
- [x] 基础对话功能
- [x] 模式控制
- [x] 工具结果展示
- [x] 侧边栏浏览

### 阶段二（计划）
- [ ] Monaco Editor 代码编辑
- [ ] ECharts 图表可视化
- [ ] 执行计划进度卡片
- [ ] 历史步骤点击回看

### 阶段三（计划）
- [ ] 多会话管理
- [ ] 主题切换（深色模式）
- [ ] 快捷键支持
- [ ] 移动端适配
