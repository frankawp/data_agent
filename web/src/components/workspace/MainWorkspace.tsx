"use client";

import React, { useState, useRef, useEffect, useCallback, ReactNode } from "react";
import { useWorkspace, StreamingStep, SubagentStep } from "@/hooks/useWorkspaceContext";
import { CodeViewer } from "@/components/data-display/CodeViewer";
import { DataTable } from "@/components/data-display/DataTable";
import { ExportsPanel } from "@/components/exports/ExportsPanel";

// Tab 类型
type WorkspaceTab = "output" | "exports";

export function MainWorkspace() {
  const {
    viewMode,
    historicalStep,
    exitHistoricalView,
    currentToolResult,
    isStreaming,
    streamingSteps,
  } = useWorkspace();

  // Tab 状态
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("output");

  // 滚动容器引用
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  // 底部标记引用
  const bottomRef = useRef<HTMLDivElement>(null);
  // 是否在底部
  const [isAtBottom, setIsAtBottom] = useState(true);
  // 是否有新内容
  const [hasNewContent, setHasNewContent] = useState(false);
  // 上一次的步骤数量
  const prevStepsCountRef = useRef(streamingSteps.length);
  // 上一次完成的步骤数量
  const prevCompletedCountRef = useRef(0);

  // 检测是否滚动到底部
  const checkIfAtBottom = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return true;

    const threshold = 100; // 距离底部 100px 内认为在底部
    const isBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
    return isBottom;
  }, []);

  // 滚动到底部
  const scrollToBottom = useCallback((smooth = true) => {
    // 使用 requestAnimationFrame 确保在 DOM 更新后滚动
    requestAnimationFrame(() => {
      const container = scrollContainerRef.current;
      if (container) {
        if (smooth) {
          container.scrollTo({
            top: container.scrollHeight,
            behavior: "smooth",
          });
        } else {
          container.scrollTop = container.scrollHeight;
        }
      }
      setHasNewContent(false);
      setIsAtBottom(true);
    });
  }, []);

  // 监听滚动事件
  const handleScroll = useCallback(() => {
    const atBottom = checkIfAtBottom();
    setIsAtBottom(atBottom);
    if (atBottom) {
      setHasNewContent(false);
    }
  }, [checkIfAtBottom]);

  // 当有新步骤时自动滚动或显示提示
  useEffect(() => {
    const currentCount = streamingSteps.length;
    const prevCount = prevStepsCountRef.current;

    if (currentCount > prevCount) {
      // 有新内容
      if (isAtBottom) {
        // 在底部时自动滚动，延迟一点确保内容渲染完成
        setTimeout(() => scrollToBottom(), 50);
      } else {
        // 不在底部时显示新内容提示
        setHasNewContent(true);
      }
    }

    prevStepsCountRef.current = currentCount;
  }, [streamingSteps.length, isAtBottom, scrollToBottom]);

  // 当步骤完成时（结果返回）也滚动到底部
  useEffect(() => {
    const completedCount = streamingSteps.filter((s) => s.status === "completed").length;
    const prevCompleted = prevCompletedCountRef.current;

    if (completedCount > prevCompleted) {
      // 有新完成的步骤
      if (isAtBottom) {
        setTimeout(() => scrollToBottom(), 100);
      } else {
        setHasNewContent(true);
      }
    }

    prevCompletedCountRef.current = completedCount;
  }, [streamingSteps, isAtBottom, scrollToBottom]);

  // 流式开始时滚动到底部
  useEffect(() => {
    if (isStreaming && streamingSteps.length === 0) {
      scrollToBottom(false);
    }
  }, [isStreaming, streamingSteps.length, scrollToBottom]);

  return (
    <div className="relative flex h-full flex-col overflow-hidden bg-white">
      {/* Tab 切换栏 */}
      <div className="flex shrink-0 border-b bg-gray-50">
        <button
          onClick={() => setActiveTab("output")}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors ${
            activeTab === "output"
              ? "border-b-2 border-blue-500 bg-white text-blue-600"
              : "text-gray-600 hover:bg-gray-100 hover:text-gray-800"
          }`}
        >
          <span>📊</span>
          <span>实时输出</span>
          {isStreaming && (
            <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
          )}
        </button>
        <button
          onClick={() => setActiveTab("exports")}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors ${
            activeTab === "exports"
              ? "border-b-2 border-blue-500 bg-white text-blue-600"
              : "text-gray-600 hover:bg-gray-100 hover:text-gray-800"
          }`}
        >
          <span>📦</span>
          <span>导出文件</span>
        </button>
      </div>

      {/* 历史模式提示条 */}
      {activeTab === "output" && viewMode === "historical" && historicalStep && (
        <div className="flex shrink-0 items-center justify-between border-b bg-amber-50 px-4 py-2">
          <span className="text-sm text-amber-800">
            正在查看历史步骤 #{historicalStep.index}: {historicalStep.toolName}
          </span>
          <button
            onClick={exitHistoricalView}
            className="rounded bg-amber-600 px-3 py-1 text-sm text-white hover:bg-amber-700"
          >
            退出历史查看 →
          </button>
        </div>
      )}

      {/* 内容区域 */}
      {activeTab === "output" ? (
        <div
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-auto p-4"
        >
          {viewMode === "live" ? (
            isStreaming || streamingSteps.length > 0 ? (
              <StreamingContent
                steps={streamingSteps}
                isStreaming={isStreaming}
              />
            ) : (
              <LiveContent toolResult={currentToolResult} />
            )
          ) : (
            <HistoricalContent step={historicalStep} />
          )}
          {/* 底部标记 */}
          <div ref={bottomRef} />
        </div>
      ) : (
        <div className="flex-1 overflow-hidden">
          <ExportsPanel />
        </div>
      )}

      {/* 新内容提示按钮 */}
      {activeTab === "output" && hasNewContent && !isAtBottom && (
        <button
          onClick={() => scrollToBottom()}
          className="absolute bottom-6 left-1/2 z-20 flex -translate-x-1/2 animate-bounce items-center gap-2 rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-lg transition-all hover:bg-blue-700"
        >
          <span>有新内容</span>
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 14l-7 7m0 0l-7-7m7 7V3"
            />
          </svg>
        </button>
      )}
    </div>
  );
}

// 流式执行内容
interface StreamingContentProps {
  steps: StreamingStep[];
  isStreaming: boolean;
}

function StreamingContent({ steps, isStreaming }: StreamingContentProps) {
  if (steps.length === 0 && isStreaming) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⚙️</div>
          <p className="text-lg">AI 正在分析任务...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 执行进度标题 */}
      <div className="flex items-center justify-between border-b pb-2">
        <h2 className="text-lg font-semibold text-gray-800">
          执行步骤 ({steps.length})
        </h2>
        {isStreaming && (
          <span className="flex items-center text-sm text-blue-600">
            <span className="mr-2 h-2 w-2 animate-pulse rounded-full bg-blue-600"></span>
            执行中...
          </span>
        )}
      </div>

      {/* 步骤列表 */}
      <div className="space-y-4">
        {steps.map((step) => (
          <StepCard key={step.step} step={step} />
        ))}
      </div>
    </div>
  );
}

// 单个步骤卡片
function StepCard({ step }: { step: StreamingStep }) {
  const statusColors = {
    running: "border-blue-500 bg-blue-50",
    completed: "border-green-500 bg-green-50",
    error: "border-red-500 bg-red-50",
  };

  const statusIcons = {
    running: "⏳",
    completed: "✅",
    error: "❌",
  };

  // 工具名称映射
  const toolNameMap: Record<string, string> = {
    execute_sql: "SQL 查询",
    execute_python_safe: "Python 执行",
    list_tables: "列出表",
    describe_table: "表结构",
    train_model: "模型训练",
    predict: "模型预测",
    create_graph: "创建图",
    graph_analysis: "图分析",
    task: "子代理任务",
    write_todos: "任务规划",
  };

  return (
    <div
      className={`rounded-lg border-l-4 p-4 ${statusColors[step.status]}`}
    >
      {/* 步骤头部 */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{statusIcons[step.status]}</span>
          <span className="font-medium text-gray-800">
            Step {step.step}: {toolNameMap[step.toolName] || step.toolName}
          </span>
        </div>
        {step.status === "running" && (
          <span className="text-xs text-blue-600 animate-pulse">执行中...</span>
        )}
      </div>

      {/* 工具参数 */}
      {step.args && Object.keys(step.args).length > 0 && (
        <div className="mb-3">
          <StepArgsDisplay toolName={step.toolName} args={step.args} />
        </div>
      )}

      {/* 子代理执行步骤（仅当 toolName 为 task 且有子步骤时显示） */}
      {step.toolName === "task" && step.subagentSteps && step.subagentSteps.length > 0 && (
        <div className="mt-3 ml-4 border-l-2 border-blue-200 pl-3 space-y-2">
          <div className="text-xs font-medium text-blue-600 flex items-center">
            <span className="mr-1">📋</span>
            {step.subagentName || "子代理"} 执行步骤:
          </div>
          {step.subagentSteps.map((substep) => (
            <SubagentStepCard
              key={`${substep.subagentName}-${substep.step}`}
              substep={substep}
            />
          ))}
        </div>
      )}

      {/* 执行结果 */}
      {step.result && (
        <div className="mt-3 border-t pt-3">
          <h4 className="text-xs font-medium text-gray-600 mb-2">执行结果:</h4>
          <StepResultDisplay toolName={step.toolName} result={step.result} />
        </div>
      )}
    </div>
  );
}

// 步骤参数显示
function StepArgsDisplay({
  toolName,
  args,
}: {
  toolName: string;
  args: Record<string, unknown>;
}) {
  switch (toolName) {
    case "execute_sql":
      return (
        <div>
          <h4 className="text-xs font-medium text-gray-600 mb-1">SQL:</h4>
          <CodeViewer code={args.query as string || ""} language="sql" />
        </div>
      );

    case "execute_python_safe":
      return (
        <div>
          <h4 className="text-xs font-medium text-gray-600 mb-1">Python 代码:</h4>
          <CodeViewer code={args.code as string || ""} language="python" />
        </div>
      );

    case "describe_table":
      return (
        <p className="text-sm text-gray-700">
          表名: <code className="bg-gray-200 px-1 rounded">{args.table_name as string}</code>
        </p>
      );

    case "train_model":
      return (
        <div className="text-sm text-gray-700 space-y-1">
          <p>模型类型: <code className="bg-gray-200 px-1 rounded">{args.model_type as string}</code></p>
          <p>目标列: <code className="bg-gray-200 px-1 rounded">{args.target_column as string}</code></p>
        </div>
      );

    case "write_todos":
      return <TodoListDisplay args={args} />;

    case "task":
      return <SubAgentCallDisplay args={args} />;

    default:
      return (
        <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-32">
          {JSON.stringify(args, null, 2)}
        </pre>
      );
  }
}

// TODO 列表显示组件
function TodoListDisplay({ args }: { args: Record<string, unknown> }) {
  const todos = args.todos as Array<{ content: string; status: string }> | undefined;

  if (!todos || !Array.isArray(todos)) {
    return null;
  }

  const statusIcons: Record<string, string> = {
    completed: "✅",
    in_progress: "🔄",
    pending: "⏳",
  };

  const statusColors: Record<string, string> = {
    completed: "text-green-600",
    in_progress: "text-blue-600",
    pending: "text-gray-500",
  };

  return (
    <div className="bg-gray-900 rounded-lg p-3">
      <h4 className="text-xs font-medium text-cyan-400 mb-2">任务进度:</h4>
      <ul className="space-y-1">
        {todos.map((todo, index) => (
          <li key={index} className="flex items-start space-x-2">
            <span className="flex-shrink-0">{statusIcons[todo.status] || "○"}</span>
            <span className={`text-sm ${statusColors[todo.status] || "text-gray-400"}`}>
              {todo.content}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// 子代理调用显示组件
function SubAgentCallDisplay({ args }: { args: Record<string, unknown> }) {
  const subagentType = args.subagent_type as string || args.agent_name as string || "unknown";
  const description = args.description as string || args.task as string || "";

  // 子代理类型图标和颜色
  const subagentInfo: Record<string, { icon: string; color: string; name: string }> = {
    "data-collector": {
      icon: "🗄️",
      color: "bg-blue-100 border-blue-300 text-blue-800",
      name: "数据采集器",
    },
    "data-analyzer": {
      icon: "📊",
      color: "bg-purple-100 border-purple-300 text-purple-800",
      name: "数据分析器",
    },
    "report-writer": {
      icon: "📝",
      color: "bg-green-100 border-green-300 text-green-800",
      name: "报告生成器",
    },
  };

  const info = subagentInfo[subagentType] || {
    icon: "🤖",
    color: "bg-gray-100 border-gray-300 text-gray-800",
    name: subagentType,
  };

  return (
    <div className={`rounded-lg border p-3 ${info.color}`}>
      <div className="flex items-center space-x-2 mb-2">
        <span className="text-xl">{info.icon}</span>
        <span className="font-medium">{info.name}</span>
        <span className="text-xs bg-white/50 px-2 py-0.5 rounded">
          {subagentType}
        </span>
      </div>
      {description && (
        <div className="text-sm mt-2 bg-white/30 rounded p-2">
          <p className="whitespace-pre-wrap">{description}</p>
        </div>
      )}
    </div>
  );
}

// 子代理步骤卡片组件
function SubagentStepCard({ substep }: { substep: SubagentStep }) {
  const statusIcons = {
    running: "⏳",
    completed: "✅",
    error: "❌",
  };

  const statusColors = {
    running: "bg-blue-50 border-blue-200",
    completed: "bg-green-50 border-green-200",
    error: "bg-red-50 border-red-200",
  };

  // 工具名称映射
  const toolNameMap: Record<string, string> = {
    execute_sql: "SQL 查询",
    execute_python_safe: "Python 执行",
    list_tables: "获取表列表",
    describe_table: "表结构分析",
    train_model: "模型训练",
    predict: "模型预测",
    create_graph: "创建图",
    graph_analysis: "图分析",
    write_todos: "任务规划",
  };

  // 根据工具和参数生成友好的描述
  const getToolDescription = (): string => {
    const { toolName, args } = substep;

    switch (toolName) {
      case "execute_sql":
        const query = (args.query as string) || "";
        if (query.toUpperCase().includes("SELECT")) {
          const tableMatch = query.match(/FROM\s+(\w+)/i);
          const tableName = tableMatch ? tableMatch[1] : "数据";
          return `查询 ${tableName} 表`;
        }
        return "执行 SQL";

      case "execute_python_safe":
        const code = (args.code as string) || "";
        if (code.includes("matplotlib") || code.includes("plt.")) {
          return "生成图表";
        }
        if (code.includes("groupby") || code.includes("agg")) {
          return "数据聚合";
        }
        return "Python 分析";

      case "describe_table":
        return `分析 ${args.table_name} 表结构`;

      case "list_tables":
        return "获取数据库表列表";

      case "write_todos":
        return "更新任务进度";

      default:
        return toolNameMap[toolName] || toolName;
    }
  };

  // 格式化结果显示
  const renderResult = () => {
    if (!substep.result) return null;

    const { toolName, result } = substep;

    // write_todos 工具显示友好提示
    if (toolName === "write_todos") {
      return (
        <div className="mt-2 text-xs text-green-600 bg-green-50 rounded px-2 py-1">
          ✓ 任务进度已更新
        </div>
      );
    }

    // [Command returned] 的情况
    if (result === "[Command returned]") {
      return (
        <div className="mt-2 text-xs text-green-600 bg-green-50 rounded px-2 py-1">
          ✓ 执行成功
        </div>
      );
    }

    // list_tables 工具 - 格式化表列表
    if (toolName === "list_tables" && result.includes("数据库中的表")) {
      const tables = result
        .replace(/^.*?[:：]\s*/, "")
        .split(/\s*-\s*/)
        .filter((t) => t.trim())
        .map((t) => t.trim());

      if (tables.length > 0) {
        return (
          <div className="mt-2 bg-white/50 rounded p-2">
            <div className="text-xs text-gray-500 mb-1">
              共 {tables.length} 个表：
            </div>
            <div className="flex flex-wrap gap-1">
              {tables.slice(0, 15).map((table, i) => (
                <span
                  key={i}
                  className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded"
                >
                  {table}
                </span>
              ))}
              {tables.length > 15 && (
                <span className="text-xs text-gray-400">
                  +{tables.length - 15} 更多...
                </span>
              )}
            </div>
          </div>
        );
      }
    }

    // describe_table 工具 - 格式化表结构
    if (toolName === "describe_table" && result.includes("表") && result.includes("的结构")) {
      return (
        <div className="mt-2 bg-white/50 rounded p-2">
          <div className="text-xs text-gray-600">
            <span className="text-green-600">✓</span> 表结构信息已获取
          </div>
        </div>
      );
    }

    // execute_python_safe 工具 - 显示 Python 代码和执行结果
    if (toolName === "execute_python_safe") {
      const pythonCode = (substep.args.code as string) || "";
      const isError = result.includes("执行失败") || result.includes("Error") || result.includes("Traceback");

      return (
        <div className="mt-2 bg-white/50 rounded p-2 overflow-hidden">
          {/* 显示 Python 代码 - 完整显示，带滚动条 */}
          {pythonCode && (
            <div className="mb-2">
              <div className="text-xs text-gray-500 mb-1">Python 代码:</div>
              <div className="p-1.5 bg-gray-800 rounded text-xs font-mono text-green-400 max-h-64 overflow-auto whitespace-pre break-all">
                {pythonCode}
              </div>
            </div>
          )}
          {/* 显示执行结果 */}
          <div className="text-xs text-gray-500 mb-1">执行结果:</div>
          <div className={`p-1.5 rounded text-xs max-h-48 overflow-auto whitespace-pre-wrap break-words ${
            isError ? "bg-red-50 text-red-700" : "bg-gray-100 text-gray-700"
          }`}>
            {result}
          </div>
        </div>
      );
    }

    // execute_sql 工具 - 格式化查询结果
    if (toolName === "execute_sql" && result.includes("查询结果")) {
      // 获取 SQL 语句
      const sqlQuery = (substep.args.query as string) || "";

      // 解析行数信息
      const rowMatch = result.match(/共\s*(\d+)\s*行/);
      const displayMatch = result.match(/显示前\s*(\d+)\s*行/);
      const totalRows = rowMatch ? rowMatch[1] : null;
      const displayRows = displayMatch ? displayMatch[1] : totalRows;

      // 尝试解析 CSV 数据
      const csvStart = result.indexOf("\n");
      if (csvStart > -1) {
        const csvData = result.slice(csvStart + 1).split("\n").filter(line =>
          line.trim() && !line.startsWith("[已导出至")
        );

        if (csvData.length > 0) {
          const headers = csvData[0].split(",").map(h => h.trim());
          const rows = csvData.slice(1, 6).map(row => row.split(",").map(c => c.trim()));

          return (
            <div className="mt-2 bg-white/50 rounded p-2 overflow-hidden">
              {/* 显示 SQL 语句 */}
              {sqlQuery && (
                <div className="mb-2 p-1.5 bg-gray-800 rounded text-xs font-mono text-green-400 overflow-x-auto whitespace-pre-wrap break-all">
                  <span className="text-gray-500 select-none">SQL: </span>
                  {sqlQuery.length > 200 ? sqlQuery.slice(0, 200) + "..." : sqlQuery}
                </div>
              )}
              <div className="text-xs text-gray-500 mb-2">
                {displayRows && totalRows && displayRows !== totalRows
                  ? `显示前 ${Math.min(5, rows.length)} 行（共 ${totalRows} 行）`
                  : `共 ${totalRows || rows.length} 行`}
              </div>
              <div className="overflow-x-auto">
                <table className="text-xs border-collapse w-full">
                  <thead>
                    <tr className="bg-gray-100">
                      {headers.slice(0, 5).map((h, i) => (
                        <th key={i} className="border border-gray-200 px-2 py-1 text-left font-medium text-gray-700">
                          {h}
                        </th>
                      ))}
                      {headers.length > 5 && (
                        <th className="border border-gray-200 px-2 py-1 text-gray-400">...</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, ri) => (
                      <tr key={ri} className={ri % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                        {row.slice(0, 5).map((cell, ci) => (
                          <td key={ci} className="border border-gray-200 px-2 py-1 text-gray-600 max-w-[120px] truncate">
                            {cell}
                          </td>
                        ))}
                        {row.length > 5 && (
                          <td className="border border-gray-200 px-2 py-1 text-gray-400">...</td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {rows.length < parseInt(totalRows || "0") && (
                <div className="text-xs text-gray-400 mt-1 text-right">
                  显示前 {rows.length} 行
                </div>
              )}
            </div>
          );
        }
      }

      // 备用：简单显示行数（也要显示 SQL）
      return (
        <div className="mt-2 bg-white/50 rounded p-2">
          {sqlQuery && (
            <div className="mb-2 p-1.5 bg-gray-800 rounded text-xs font-mono text-green-400 overflow-x-auto whitespace-pre-wrap break-all">
              <span className="text-gray-500 select-none">SQL: </span>
              {sqlQuery.length > 200 ? sqlQuery.slice(0, 200) + "..." : sqlQuery}
            </div>
          )}
          <div className="text-xs text-gray-600">
            ✓ 查询完成，共 {totalRows || "?"} 行数据
          </div>
        </div>
      );
    }

    // 默认显示：使用滚动条而非截断
    return (
      <div className="mt-2 text-xs text-gray-600 bg-white/50 rounded p-1.5 whitespace-pre-wrap break-words max-h-48 overflow-auto">
        {result}
      </div>
    );
  };

  return (
    <div className={`rounded border p-2 text-sm ${statusColors[substep.status]}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span>{statusIcons[substep.status]}</span>
          <span className="font-medium text-gray-700">
            {getToolDescription()}
          </span>
        </div>
        {substep.status === "running" && (
          <span className="text-xs text-blue-500 animate-pulse">执行中...</span>
        )}
      </div>

      {/* 显示格式化后的结果 */}
      {renderResult()}
    </div>
  );
}

// 步骤结果显示
function StepResultDisplay({
  toolName,
  result,
}: {
  toolName: string;
  result: string;
}) {
  // 限制结果显示长度
  const maxLength = 3000;
  const truncatedResult =
    result.length > maxLength
      ? result.slice(0, maxLength) + "\n... (结果已截断)"
      : result;

  switch (toolName) {
    case "execute_sql":
      return <DataTable data={parseTableData(result)} />;

    case "task":
      return <MarkdownDisplay content={truncatedResult} />;

    default:
      return (
        <pre className="text-xs bg-gray-900 text-gray-100 p-3 rounded overflow-auto max-h-64">
          {truncatedResult}
        </pre>
      );
  }
}

// 简单的 Markdown 渲染组件
function MarkdownDisplay({ content }: { content: string }) {
  // 将 markdown 转换为 HTML（简化版本）
  const renderMarkdown = (text: string) => {
    const lines = text.split("\n");
    const elements: ReactNode[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];
    let inTable = false;
    let tableRows: string[][] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // 代码块处理
      if (line.startsWith("```")) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeBlockContent = [];
        } else {
          inCodeBlock = false;
          elements.push(
            <pre key={`code-${i}`} className="bg-gray-900 text-gray-100 p-3 rounded text-xs overflow-auto my-2">
              <code>{codeBlockContent.join("\n")}</code>
            </pre>
          );
        }
        continue;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        continue;
      }

      // 表格处理
      if (line.includes("|") && line.trim().startsWith("|")) {
        if (!inTable) {
          inTable = true;
          tableRows = [];
        }
        // 跳过分隔符行
        if (line.match(/^\|[\s\-:|]+\|$/)) {
          continue;
        }
        const cells = line.split("|").filter(c => c.trim() !== "").map(c => c.trim());
        tableRows.push(cells);
        continue;
      } else if (inTable) {
        // 表格结束
        inTable = false;
        if (tableRows.length > 0) {
          elements.push(
            <div key={`table-${i}`} className="overflow-auto my-2">
              <table className="min-w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-100">
                    {tableRows[0].map((cell, j) => (
                      <th key={j} className="border border-gray-300 px-3 py-1 text-left font-medium">
                        {cell}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableRows.slice(1).map((row, ri) => (
                    <tr key={ri} className={ri % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                      {row.map((cell, ci) => (
                        <td key={ci} className="border border-gray-300 px-3 py-1">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
          tableRows = [];
        }
      }

      // 空行
      if (!line.trim()) {
        elements.push(<div key={`space-${i}`} className="h-2" />);
        continue;
      }

      // 标题
      if (line.startsWith("### ")) {
        elements.push(
          <h4 key={`h4-${i}`} className="text-sm font-semibold text-gray-800 mt-3 mb-1">
            {line.slice(4)}
          </h4>
        );
        continue;
      }
      if (line.startsWith("## ")) {
        elements.push(
          <h3 key={`h3-${i}`} className="text-base font-semibold text-gray-800 mt-4 mb-2">
            {line.slice(3)}
          </h3>
        );
        continue;
      }
      if (line.startsWith("# ")) {
        elements.push(
          <h2 key={`h2-${i}`} className="text-lg font-bold text-gray-900 mt-4 mb-2">
            {line.slice(2)}
          </h2>
        );
        continue;
      }

      // 列表项
      if (line.match(/^[\s]*[-*]\s/)) {
        const indent = line.match(/^[\s]*/)?.[0].length || 0;
        const content = line.replace(/^[\s]*[-*]\s/, "");
        elements.push(
          <div key={`li-${i}`} className="flex items-start" style={{ paddingLeft: `${indent * 0.5}rem` }}>
            <span className="text-gray-400 mr-2">•</span>
            <span className="text-sm text-gray-700">{renderInlineMarkdown(content)}</span>
          </div>
        );
        continue;
      }

      // 数字列表
      if (line.match(/^[\s]*\d+\.\s/)) {
        const match = line.match(/^[\s]*(\d+)\.\s(.*)$/);
        if (match) {
          elements.push(
            <div key={`oli-${i}`} className="flex items-start">
              <span className="text-gray-500 mr-2 min-w-[1.5rem]">{match[1]}.</span>
              <span className="text-sm text-gray-700">{renderInlineMarkdown(match[2])}</span>
            </div>
          );
          continue;
        }
      }

      // 普通段落
      elements.push(
        <p key={`p-${i}`} className="text-sm text-gray-700 my-1">
          {renderInlineMarkdown(line)}
        </p>
      );
    }

    // 处理文件末尾的表格
    if (inTable && tableRows.length > 0) {
      elements.push(
        <div key="table-end" className="overflow-auto my-2">
          <table className="min-w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100">
                {tableRows[0].map((cell, j) => (
                  <th key={j} className="border border-gray-300 px-3 py-1 text-left font-medium">
                    {cell}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.slice(1).map((row, ri) => (
                <tr key={ri} className={ri % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                  {row.map((cell, ci) => (
                    <td key={ci} className="border border-gray-300 px-3 py-1">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    return elements;
  };

  // 处理行内 markdown（粗体、斜体、代码）
  const renderInlineMarkdown = (text: string) => {
    // 简单处理：将 **text** 转为粗体，`code` 转为代码样式
    const parts: ReactNode[] = [];
    let remaining = text;
    let keyIndex = 0;

    while (remaining.length > 0) {
      // 匹配粗体
      const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
      // 匹配行内代码
      const codeMatch = remaining.match(/`([^`]+)`/);

      if (boldMatch && (!codeMatch || remaining.indexOf(boldMatch[0]) < remaining.indexOf(codeMatch[0]))) {
        const index = remaining.indexOf(boldMatch[0]);
        if (index > 0) {
          parts.push(remaining.slice(0, index));
        }
        parts.push(
          <strong key={`bold-${keyIndex++}`} className="font-semibold">
            {boldMatch[1]}
          </strong>
        );
        remaining = remaining.slice(index + boldMatch[0].length);
      } else if (codeMatch) {
        const index = remaining.indexOf(codeMatch[0]);
        if (index > 0) {
          parts.push(remaining.slice(0, index));
        }
        parts.push(
          <code key={`code-${keyIndex++}`} className="bg-gray-200 px-1 rounded text-sm">
            {codeMatch[1]}
          </code>
        );
        remaining = remaining.slice(index + codeMatch[0].length);
      } else {
        parts.push(remaining);
        break;
      }
    }

    return <>{parts}</>;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 max-h-96 overflow-auto">
      {renderMarkdown(content)}
    </div>
  );
}

interface LiveContentProps {
  toolResult: {
    toolName: string;
    args: Record<string, unknown>;
    result: string;
  } | null;
}

function LiveContent({ toolResult }: LiveContentProps) {
  if (!toolResult) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <p className="text-lg">等待 AI 执行操作...</p>
          <p className="text-sm mt-2">
            与右侧的数据分析助手对话，这里将显示执行的具体内容
          </p>
        </div>
      </div>
    );
  }

  return <ToolResultDisplay toolResult={toolResult} />;
}

interface HistoricalContentProps {
  step: {
    index: number;
    toolName: string;
    args: Record<string, unknown>;
    result: string;
  } | null;
}

function HistoricalContent({ step }: HistoricalContentProps) {
  if (!step) {
    return null;
  }

  return (
    <ToolResultDisplay
      toolResult={{
        toolName: step.toolName,
        args: step.args,
        result: step.result,
      }}
    />
  );
}

interface ToolResultDisplayProps {
  toolResult: {
    toolName: string;
    args: Record<string, unknown>;
    result: string;
  };
}

function ToolResultDisplay({ toolResult }: ToolResultDisplayProps) {
  const { toolName, args, result } = toolResult;

  // 根据工具类型渲染不同的内容
  switch (toolName) {
    case "execute_sql":
      return (
        <div className="space-y-4">
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">
              SQL 查询
            </h3>
            <CodeViewer code={args.query as string} language="sql" />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">
              查询结果
            </h3>
            <DataTable data={parseTableData(result)} />
          </div>
        </div>
      );

    case "execute_python_safe":
      return (
        <div className="space-y-4">
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">
              Python 代码
            </h3>
            <CodeViewer code={args.code as string} language="python" />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">
              执行输出
            </h3>
            <pre className="rounded-lg bg-gray-900 p-4 text-sm text-gray-100 overflow-auto">
              {result}
            </pre>
          </div>
        </div>
      );

    case "train_model":
      return (
        <div className="space-y-4">
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">
              模型训练
            </h3>
            <div className="rounded-lg border p-4">
              <p>
                <strong>模型类型:</strong> {args.model_type as string}
              </p>
              <p>
                <strong>目标列:</strong> {args.target_column as string}
              </p>
            </div>
          </div>
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">
              训练结果
            </h3>
            <pre className="rounded-lg bg-gray-100 p-4 text-sm overflow-auto">
              {result}
            </pre>
          </div>
        </div>
      );

    case "describe_table":
      return (
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-700">
            表结构: {args.table_name as string}
          </h3>
          <pre className="rounded-lg bg-gray-100 p-4 text-sm overflow-auto">
            {result}
          </pre>
        </div>
      );

    default:
      return (
        <div className="space-y-4">
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">
              {toolName}
            </h3>
            <pre className="rounded-lg bg-gray-100 p-4 text-sm overflow-auto">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">结果</h3>
            <pre className="rounded-lg bg-gray-100 p-4 text-sm overflow-auto">
              {result}
            </pre>
          </div>
        </div>
      );
  }
}

// 解析 CSV 格式的表格数据
function parseTableData(result: string): { columns: string[]; rows: string[][] } {
  const lines = result.trim().split("\n");
  if (lines.length === 0) {
    return { columns: [], rows: [] };
  }

  // 跳过开头的摘要行（如 "查询结果（共 X 行）:"）
  let dataStartIndex = 0;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith("查询结果") || line.startsWith("[已导出至")) {
      dataStartIndex = i + 1;
      continue;
    }
    // 找到第一个非空、非摘要的行作为表头
    if (line && !line.startsWith("查询结果") && !line.startsWith("[已导出至")) {
      dataStartIndex = i;
      break;
    }
  }

  const dataLines = lines.slice(dataStartIndex).filter((line) => {
    const trimmed = line.trim();
    return trimmed && !trimmed.startsWith("[已导出至");
  });

  if (dataLines.length === 0) {
    return { columns: [], rows: [] };
  }

  // 解析 CSV（处理引号内的逗号）
  const parseCSVLine = (line: string): string[] => {
    const result: string[] = [];
    let current = "";
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === "," && !inQuotes) {
        result.push(current.trim());
        current = "";
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  };

  // 第一行是列名
  const columns = parseCSVLine(dataLines[0]);
  const rows = dataLines.slice(1).map((line) => parseCSVLine(line));

  return { columns, rows };
}
