"use client";

/**
 * 聊天侧边栏组件
 *
 * 使用 Assistant UI 组件库提供专业的 AI Agent 聊天界面。
 * 支持工具调用显示、流式响应、用户中断等功能。
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { useWorkspace, StreamingStep } from "@/hooks/useWorkspaceContext";
import { useSession } from "@/providers/SessionProvider";

interface ChatSidebarProps {
  className?: string;
}

export function ChatSidebar({ className }: ChatSidebarProps) {
  const { sessionId } = useSession();
  const {
    setCurrentToolResult,
    clearHistory,
    startStreaming,
    addStreamingStep,
    updateStreamingStepResult,
    finishStreaming,
    isStreaming,
    streamingSteps,
    addSubagentStep,
    updateSubagentStepResult,
  } = useWorkspace();

  const [messages, setMessages] = useState<
    Array<{
      id: string;
      role: "user" | "assistant";
      content: string;
    }>
  >([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 处理 SSE 事件
  const handleSSEEvent = useCallback(
    (eventType: string, data: Record<string, unknown>) => {
      switch (eventType) {
        case "tool_call":
          addStreamingStep({
            step: data.step as number,
            toolName: data.tool_name as string,
            args: data.args as Record<string, unknown>,
          });
          break;

        case "tool_result":
          updateStreamingStepResult(
            data.step as number,
            data.result as string,
            data.tool_name as string
          );
          setCurrentToolResult({
            toolName: data.tool_name as string,
            args: {},
            result: data.result as string,
          });
          break;

        case "thinking":
          console.log("AI thinking:", data.content);
          break;

        case "subagent_tool_call":
          addSubagentStep({
            subagentName: data.subagent_name as string,
            step: data.step as number,
            toolName: data.tool_name as string,
            args: data.args as Record<string, unknown>,
          });
          break;

        case "subagent_tool_result":
          updateSubagentStepResult({
            subagentName: data.subagent_name as string,
            step: data.step as number,
            result: data.result as string,
          });
          break;

        case "message":
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
    [
      addStreamingStep,
      updateStreamingStepResult,
      setCurrentToolResult,
      finishStreaming,
      addSubagentStep,
      updateSubagentStepResult,
    ]
  );

  // 发送消息
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user" as const,
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const assistantId = `assistant-${Date.now()}`;
    setMessages((prev) => [...prev, { id: assistantId, role: "assistant", content: "" }]);

    startStreaming();
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage].map((m) => ({
            role: m.role,
            content: m.content,
          })),
          session_id: sessionId,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalContent = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

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

      const assistantContent = finalContent || "任务完成。";
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, content: assistantContent } : m))
      );
    } catch (error) {
      if ((error as Error).name !== "AbortError") {
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
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  // 取消请求
  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      finishStreaming();
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
      await fetch(`/api/chat/reset?session_id=${sessionId || "default"}`, { method: "POST" });
      setMessages([]);
      setCurrentToolResult(null);
      clearHistory();
    } catch (error) {
      console.error("Reset error:", error);
    }
  };

  return (
    <aside className={`flex h-full flex-col border-l bg-white ${className}`}>
      {/* Header */}
      <div className="flex shrink-0 items-center justify-between border-b bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
          </div>
          <div>
            <h2 className="font-semibold text-gray-800">数据分析助手</h2>
            <p className="text-xs text-gray-500">AI 驱动的智能分析</p>
          </div>
        </div>
        <button
          onClick={clearChat}
          className="rounded-lg px-3 py-1.5 text-sm text-gray-500 transition-colors hover:bg-white hover:text-gray-700 hover:shadow-sm"
        >
          清空对话
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <WelcomeMessage />
        ) : (
          <div className="space-y-1 p-4">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isLoading={isLoading && message.role === "assistant" && !message.content}
                streamingSteps={streamingSteps}
                isStreaming={isStreaming}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="shrink-0 border-t bg-gray-50 p-4">
        {/* 停止按钮 */}
        {isLoading && (
          <div className="mb-3 flex justify-center">
            <button
              onClick={handleCancel}
              className="flex items-center gap-2 rounded-full bg-red-100 px-4 py-1.5 text-sm text-red-600 transition-colors hover:bg-red-200"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
                />
              </svg>
              停止生成
            </button>
          </div>
        )}

        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="描述您的数据分析需求..."
            disabled={isLoading}
            rows={2}
            className="flex-1 resize-none rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm shadow-sm transition-all focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 disabled:bg-gray-100"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="flex h-auto items-center justify-center rounded-xl bg-blue-600 px-4 text-white shadow-sm transition-all hover:bg-blue-700 hover:shadow-md disabled:cursor-not-allowed disabled:bg-gray-300"
          >
            {isLoading ? (
              <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            )}
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-gray-400">
          按 Enter 发送，Shift + Enter 换行
        </p>
      </div>
    </aside>
  );
}

// 欢迎消息
function WelcomeMessage() {
  return (
    <div className="flex h-full flex-col items-center justify-center p-6 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg">
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
          />
        </svg>
      </div>
      <h3 className="mb-2 text-lg font-semibold text-gray-800">数据分析助手</h3>
      <p className="mb-6 max-w-sm text-sm text-gray-500">
        我可以帮助您进行数据查询、分析和可视化。请描述您的需求，我将自动规划和执行任务。
      </p>

      <div className="grid w-full max-w-sm gap-2">
        <SuggestionButton text="分析数据库中的表结构" />
        <SuggestionButton text="查询销售数据并生成报表" />
        <SuggestionButton text="训练一个预测模型" />
      </div>
    </div>
  );
}

// 建议按钮
function SuggestionButton({ text }: { text: string }) {
  return (
    <button className="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-left text-sm text-gray-600 transition-all hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 hover:shadow-sm">
      <span className="mr-2 text-blue-500">→</span>
      {text}
    </button>
  );
}

// 消息气泡
interface MessageBubbleProps {
  message: { id: string; role: "user" | "assistant"; content: string };
  isLoading: boolean;
  streamingSteps: StreamingStep[];
  isStreaming: boolean;
}

function MessageBubble({ message, isLoading, streamingSteps, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-white text-gray-800 shadow-sm ring-1 ring-gray-100"
        }`}
      >
        {message.content ? (
          <div className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</div>
        ) : isLoading ? (
          <StreamingStatus steps={streamingSteps} isStreaming={isStreaming} />
        ) : null}
      </div>
    </div>
  );
}

// 流式执行状态组件
interface StreamingStatusProps {
  steps: StreamingStep[];
  isStreaming: boolean;
}

function StreamingStatus({ steps, isStreaming }: StreamingStatusProps) {
  const currentStep = steps.find((s) => s.status === "running");
  const completedCount = steps.filter((s) => s.status === "completed").length;
  const totalSteps = steps.length;

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
    task: "子代理任务",
  };

  const getStepDescription = (step: StreamingStep): string => {
    const { toolName, args } = step;

    switch (toolName) {
      case "execute_sql":
        const query = (args.query as string) || "";
        if (query.toUpperCase().includes("SELECT")) {
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
        if (code.includes("groupby") || code.includes("agg")) {
          return "正在进行数据聚合统计...";
        }
        return "正在执行 Python 数据分析...";

      case "describe_table":
        return `正在分析 ${args.table_name} 表结构...`;

      case "list_tables":
        return "正在获取数据库表列表...";

      case "train_model":
        return `正在训练 ${args.model_type || "机器学习"} 模型...`;

      case "task":
        return `正在执行子任务: ${args.description || ""}`;

      case "write_todos":
        return "正在规划分析任务...";

      default:
        return `正在执行 ${toolNameMap[toolName] || toolName}...`;
    }
  };

  if (totalSteps === 0 && isStreaming) {
    return (
      <div className="flex items-center space-x-2 py-1">
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
        <span className="text-xs text-gray-500">AI 正在分析您的需求...</span>
      </div>
    );
  }

  return (
    <div className="min-w-[200px] space-y-2">
      {/* 进度指示器 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="h-2 w-2 animate-pulse rounded-full bg-blue-500"></div>
          <span className="text-xs font-medium text-gray-700">
            步骤 {completedCount + (currentStep ? 1 : 0)}/{totalSteps}
          </span>
        </div>
        {isStreaming && <span className="text-xs text-blue-600">执行中</span>}
      </div>

      {/* 进度条 */}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-300"
          style={{
            width: `${totalSteps > 0 ? (completedCount / totalSteps) * 100 : 0}%`,
          }}
        />
      </div>

      {/* 当前步骤描述 */}
      {currentStep && (
        <p className="text-xs leading-relaxed text-gray-600">{getStepDescription(currentStep)}</p>
      )}

      {/* 已完成的步骤摘要 */}
      {completedCount > 0 && (
        <div className="mt-2 space-y-0.5 border-t pt-2 text-xs text-gray-500">
          {steps
            .filter((s) => s.status === "completed")
            .slice(-3)
            .map((step, idx) => (
              <div key={idx} className="flex items-center space-x-1">
                <span className="text-green-500">✓</span>
                <span className="truncate">{toolNameMap[step.toolName] || step.toolName}</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

export default ChatSidebar;
