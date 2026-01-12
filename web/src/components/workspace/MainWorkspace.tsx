"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useWorkspace, StreamingStep } from "@/hooks/useWorkspaceContext";
import { CodeViewer } from "@/components/data-display/CodeViewer";
import { DataTable } from "@/components/data-display/DataTable";

export function MainWorkspace() {
  const {
    viewMode,
    historicalStep,
    exitHistoricalView,
    currentToolResult,
    isStreaming,
    streamingSteps,
  } = useWorkspace();

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
    <div className="relative h-full overflow-hidden bg-white">
      {/* 历史模式提示条 */}
      {viewMode === "historical" && historicalStep && (
        <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between border-b bg-amber-50 px-4 py-2">
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
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className={`h-full overflow-auto p-4 ${
          viewMode === "historical" ? "pt-14" : ""
        }`}
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

      {/* 新内容提示按钮 */}
      {hasNewContent && !isAtBottom && (
        <button
          onClick={() => scrollToBottom()}
          className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-lg hover:bg-blue-700 transition-all animate-bounce"
        >
          <span>有新内容</span>
          <svg
            className="w-4 h-4"
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

// 步骤结果显示
function StepResultDisplay({
  toolName,
  result,
}: {
  toolName: string;
  result: string;
}) {
  // 限制结果显示长度
  const maxLength = 2000;
  const truncatedResult =
    result.length > maxLength
      ? result.slice(0, maxLength) + "\n... (结果已截断)"
      : result;

  switch (toolName) {
    case "execute_sql":
      return <DataTable data={parseTableData(result)} />;

    default:
      return (
        <pre className="text-xs bg-gray-900 text-gray-100 p-3 rounded overflow-auto max-h-64">
          {truncatedResult}
        </pre>
      );
  }
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
