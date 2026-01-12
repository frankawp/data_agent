"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useWorkspace, StreamingStep } from "@/hooks/useWorkspaceContext";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatSidebarProps {
  className?: string;
}

export function ChatSidebar({ className }: ChatSidebarProps) {
  const {
    setCurrentToolResult,
    clearHistory,
    startStreaming,
    addStreamingStep,
    updateStreamingStepResult,
    finishStreaming,
    isStreaming,
    streamingSteps,
  } = useWorkspace();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial",
      role: "assistant",
      content: "我可以帮助您进行数据查询、分析和可视化。请描述您的需求。",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 处理 SSE 事件
  const handleSSEEvent = useCallback(
    (eventType: string, data: Record<string, unknown>) => {
      switch (eventType) {
        case "tool_call":
          // 工具调用开始
          addStreamingStep({
            step: data.step as number,
            toolName: data.tool_name as string,
            args: data.args as Record<string, unknown>,
          });
          break;

        case "tool_result":
          // 工具执行结果
          updateStreamingStepResult(
            data.step as number,
            data.result as string
          );
          // 同时更新当前工具结果用于显示
          setCurrentToolResult({
            toolName: data.tool_name as string,
            args: {},
            result: data.result as string,
          });
          break;

        case "thinking":
          // AI 思考内容（可选显示）
          console.log("AI thinking:", data.content);
          break;

        case "message":
          // 最终消息
          return data.content as string;

        case "error":
          console.error("Stream error:", data.error);
          return `错误: ${data.error}`;

        case "done":
          finishStreaming();
          break;
      }
      return null;
    },
    [addStreamingStep, updateStreamingStepResult, setCurrentToolResult, finishStreaming]
  );

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // 创建临时的助手消息
    const assistantId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "" },
    ]);

    // 开始流式执行
    startStreaming();

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage].map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // 处理 SSE 流
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalContent = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // 解析 SSE 事件
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // 保留未完成的行

          let currentEvent = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const dataStr = line.slice(6);
              try {
                const data = JSON.parse(dataStr);
                const result = handleSSEEvent(currentEvent, data);
                if (result) {
                  finalContent = result;
                }
              } catch {
                // 忽略解析错误
              }
            }
          }
        }
      }

      // 更新最终消息
      const assistantContent = finalContent || "任务完成。";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, content: assistantContent } : m
        )
      );
    } catch (error) {
      console.error("Chat error:", error);
      finishStreaming();
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: `发送失败: ${error instanceof Error ? error.message : "未知错误"}`,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = async () => {
    try {
      await fetch("/api/chat/reset", { method: "POST" });
      setMessages([
        {
          id: "initial",
          role: "assistant",
          content: "我可以帮助您进行数据查询、分析和可视化。请描述您的需求。",
        },
      ]);
      setCurrentToolResult(null);
      clearHistory();
    } catch (error) {
      console.error("Reset error:", error);
    }
  };

  return (
    <aside className={`flex h-full flex-col border-l bg-white ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h2 className="text-lg font-semibold text-gray-800">数据分析助手</h2>
        <button
          onClick={clearChat}
          className="rounded px-2 py-1 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700"
        >
          清空
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-4 py-2 ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {message.content ? (
                <p className="whitespace-pre-wrap text-sm">{message.content}</p>
              ) : isLoading && message.role === "assistant" ? (
                <StreamingStatus
                  steps={streamingSteps}
                  isStreaming={isStreaming}
                />
              ) : null}
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="描述您的数据分析需求..."
            disabled={isLoading}
            rows={2}
            className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isLoading ? "..." : "发送"}
          </button>
        </div>
      </div>
    </aside>
  );
}

// 流式执行状态组件
interface StreamingStatusProps {
  steps: StreamingStep[];
  isStreaming: boolean;
}

function StreamingStatus({ steps, isStreaming }: StreamingStatusProps) {
  // 获取当前正在执行的步骤
  const currentStep = steps.find((s) => s.status === "running");
  const completedCount = steps.filter((s) => s.status === "completed").length;
  const totalSteps = steps.length;

  // 工具名称映射
  const toolNameMap: Record<string, string> = {
    execute_sql: "SQL 查询",
    execute_python_safe: "Python 分析",
    list_tables: "获取表列表",
    describe_table: "分析表结构",
    train_model: "训练模型",
    predict: "模型预测",
    create_graph: "创建图",
    graph_analysis: "图分析",
    write_todos: "规划任务",
  };

  // 根据工具和参数生成友好的描述
  const getStepDescription = (step: StreamingStep): string => {
    const { toolName, args } = step;

    switch (toolName) {
      case "execute_sql":
        const query = (args.query as string) || "";
        if (query.toUpperCase().includes("SELECT")) {
          // 尝试提取表名
          const tableMatch = query.match(/FROM\s+(\w+)/i);
          const tableName = tableMatch ? tableMatch[1] : "数据";
          return `正在查询 ${tableName} 表数据...`;
        }
        return "正在执行 SQL 查询...";

      case "execute_python_safe":
        const code = (args.code as string) || "";
        if (code.includes("matplotlib") || code.includes("plt.")) {
          return "正在生成数据可视化图表...";
        }
        if (code.includes("correlation") || code.includes("corr")) {
          return "正在计算相关性分析...";
        }
        if (code.includes("groupby") || code.includes("agg")) {
          return "正在进行数据聚合统计...";
        }
        if (code.includes("merge") || code.includes("join")) {
          return "正在关联多个数据表...";
        }
        if (code.includes("describe") || code.includes("统计")) {
          return "正在进行描述性统计分析...";
        }
        return "正在执行 Python 数据分析...";

      case "describe_table":
        const tableName = args.table_name as string;
        return `正在分析 ${tableName} 表结构...`;

      case "list_tables":
        return "正在获取数据库表列表...";

      case "train_model":
        const modelType = args.model_type as string;
        return `正在训练 ${modelType || "机器学习"} 模型...`;

      case "predict":
        return "正在进行模型预测...";

      case "write_todos":
        return "正在规划分析任务...";

      default:
        return `正在执行 ${toolNameMap[toolName] || toolName}...`;
    }
  };

  // 没有步骤时显示初始状态
  if (totalSteps === 0 && isStreaming) {
    return (
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div className="h-2 w-2 animate-bounce rounded-full bg-blue-400"></div>
            <div
              className="h-2 w-2 animate-bounce rounded-full bg-blue-400"
              style={{ animationDelay: "0.1s" }}
            ></div>
            <div
              className="h-2 w-2 animate-bounce rounded-full bg-blue-400"
              style={{ animationDelay: "0.2s" }}
            ></div>
          </div>
        </div>
        <p className="text-xs text-gray-600">AI 正在分析您的需求...</p>
      </div>
    );
  }

  return (
    <div className="space-y-2 min-w-[200px]">
      {/* 进度指示器 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="h-2 w-2 animate-pulse rounded-full bg-blue-500"></div>
          <span className="text-xs font-medium text-gray-700">
            步骤 {completedCount + (currentStep ? 1 : 0)}/{totalSteps}
          </span>
        </div>
        {isStreaming && (
          <span className="text-xs text-blue-600">执行中</span>
        )}
      </div>

      {/* 进度条 */}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-300"
          style={{
            width: `${totalSteps > 0 ? (completedCount / totalSteps) * 100 : 0}%`,
          }}
        />
      </div>

      {/* 当前步骤描述 */}
      {currentStep && (
        <p className="text-xs text-gray-600 leading-relaxed">
          {getStepDescription(currentStep)}
        </p>
      )}

      {/* 已完成的关键步骤摘要 */}
      {completedCount > 0 && (
        <div className="text-xs text-gray-500 space-y-0.5 border-t pt-2 mt-2">
          {steps
            .filter((s) => s.status === "completed")
            .slice(-3) // 只显示最近3个
            .map((step, idx) => (
              <div key={idx} className="flex items-center space-x-1">
                <span className="text-green-500">✓</span>
                <span className="truncate">
                  {toolNameMap[step.toolName] || step.toolName}
                </span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
