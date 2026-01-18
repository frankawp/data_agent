"use client";

/**
 * 聊天侧边栏组件
 *
 * 使用 Ant Design 组件库重构的 AI Agent 聊天界面。
 * 支持工具调用显示、流式响应、用户中断等功能。
 */

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Button,
  Input,
  Typography,
  Space,
  Progress,
  Tag,
  Spin,
  Card,
} from "antd";
import {
  SendOutlined,
  ClearOutlined,
  StopOutlined,
  MessageOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  BulbOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useWorkspace, StreamingStep } from "@/hooks/useWorkspaceContext";
import { useSession } from "@/providers/SessionProvider";

const { TextArea } = Input;
const { Text, Title } = Typography;

export function ChatSidebar() {
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
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#fff" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 16px",
          borderBottom: "1px solid #f0f0f0",
          background: "linear-gradient(to right, #eff6ff, #eef2ff)",
        }}
      >
        <Space>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: "#2563eb",
              color: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <MessageOutlined />
          </div>
          <div>
            <Title level={5} style={{ margin: 0, fontSize: 14 }}>
              数据分析助手
            </Title>
            <Text type="secondary" style={{ fontSize: 12 }}>
              AI 驱动的智能分析
            </Text>
          </div>
        </Space>
        <Button type="text" icon={<ClearOutlined />} onClick={clearChat}>
          清空对话
        </Button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflow: "auto", padding: messages.length > 0 ? 16 : 0 }}>
        {messages.length === 0 ? (
          <WelcomeMessage />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
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
      <div style={{ borderTop: "1px solid #f0f0f0", background: "#fafafa", padding: 16 }}>
        {/* 停止按钮 */}
        {isLoading && (
          <div style={{ textAlign: "center", marginBottom: 12 }}>
            <Button
              danger
              icon={<StopOutlined />}
              onClick={handleCancel}
              style={{ borderRadius: 20 }}
            >
              停止生成
            </Button>
          </div>
        )}

        <Space.Compact style={{ width: "100%" }}>
          <TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="描述您的数据分析需求..."
            disabled={isLoading}
            rows={2}
            style={{ borderRadius: "12px 0 0 12px", resize: "none" }}
          />
          <Button
            type="primary"
            icon={isLoading ? <LoadingOutlined /> : <SendOutlined />}
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            style={{ height: "auto", borderRadius: "0 12px 12px 0" }}
          />
        </Space.Compact>
        <Text type="secondary" style={{ display: "block", textAlign: "center", marginTop: 8, fontSize: 12 }}>
          按 Enter 发送，Shift + Enter 换行
        </Text>
      </div>
    </div>
  );
}

// 欢迎消息
function WelcomeMessage() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        padding: 24,
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: 16,
          background: "linear-gradient(135deg, #3b82f6, #4f46e5)",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 32,
          marginBottom: 16,
          boxShadow: "0 10px 25px rgba(59, 130, 246, 0.3)",
        }}
      >
        <BulbOutlined />
      </div>
      <Title level={4} style={{ marginBottom: 8 }}>
        数据分析助手
      </Title>
      <Text type="secondary" style={{ maxWidth: 280, marginBottom: 24 }}>
        我可以帮助您进行数据查询、分析和可视化。请描述您的需求，我将自动规划和执行任务。
      </Text>

      <Space orientation="vertical" style={{ width: "100%", maxWidth: 280 }}>
        <SuggestionButton text="分析数据库中的表结构" />
        <SuggestionButton text="查询销售数据并生成报表" />
        <SuggestionButton text="训练一个预测模型" />
      </Space>
    </div>
  );
}

// 建议按钮
function SuggestionButton({ text }: { text: string }) {
  return (
    <Button
      block
      style={{
        height: "auto",
        padding: "10px 16px",
        textAlign: "left",
        borderRadius: 8,
      }}
    >
      <Text type="secondary" style={{ marginRight: 8 }}>→</Text>
      {text}
    </Button>
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
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <Card
        size="small"
        style={{
          maxWidth: "85%",
          borderRadius: 16,
          background: isUser ? "#2563eb" : "#fff",
          border: isUser ? "none" : "1px solid #f0f0f0",
        }}
        styles={{ body: { padding: "10px 16px" } }}
      >
        {message.content ? (
          isUser ? (
            // 用户消息 - 纯文本
            <Text style={{ color: "#fff", whiteSpace: "pre-wrap" }}>
              {message.content}
            </Text>
          ) : (
            // AI 回复 - Markdown 渲染
            <div style={{ color: "#333", fontSize: 14, lineHeight: 1.6 }}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => <p style={{ margin: "4px 0" }}>{children}</p>,
                  ul: ({ children }) => <ul style={{ margin: "4px 0", paddingLeft: 20 }}>{children}</ul>,
                  ol: ({ children }) => <ol style={{ margin: "4px 0", paddingLeft: 20 }}>{children}</ol>,
                  li: ({ children }) => <li style={{ margin: "2px 0" }}>{children}</li>,
                  strong: ({ children }) => <strong style={{ color: "#389e0d", fontWeight: 600 }}>{children}</strong>,
                  code: ({ children, className }) => {
                    if (className) return <code>{children}</code>;
                    return (
                      <code style={{ background: "#f0f0f0", padding: "1px 4px", borderRadius: 3, fontSize: "0.9em" }}>
                        {children}
                      </code>
                    );
                  },
                  pre: ({ children }) => (
                    <pre style={{ background: "#1a1a2e", color: "#e0e0e0", padding: 8, borderRadius: 4, overflow: "auto", fontSize: 12, margin: "4px 0" }}>
                      {children}
                    </pre>
                  ),
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#1890ff" }}>
                      {children}
                    </a>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )
        ) : isLoading ? (
          <StreamingStatus steps={streamingSteps} isStreaming={isStreaming} />
        ) : null}
      </Card>
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
      <Space>
        <Spin size="small" />
        <Text type="secondary" style={{ fontSize: 12 }}>
          AI 正在分析您的需求...
        </Text>
      </Space>
    );
  }

  const percent = totalSteps > 0 ? Math.round((completedCount / totalSteps) * 100) : 0;

  return (
    <div style={{ minWidth: 200 }}>
      {/* 进度指示器 */}
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        <Space size={4}>
          <RobotOutlined style={{ color: "#2563eb" }} />
          <Text style={{ fontSize: 12 }}>
            步骤 {completedCount + (currentStep ? 1 : 0)}/{totalSteps}
          </Text>
        </Space>
        {isStreaming && (
          <Tag color="processing" style={{ marginRight: 0 }}>
            执行中
          </Tag>
        )}
      </div>

      {/* 进度条 */}
      <Progress
        percent={percent}
        size="small"
        strokeColor={{ from: "#3b82f6", to: "#4f46e5" }}
        showInfo={false}
      />

      {/* 当前步骤描述 */}
      {currentStep && (
        <Text type="secondary" style={{ fontSize: 12, display: "block", marginTop: 8 }}>
          {getStepDescription(currentStep)}
        </Text>
      )}

      {/* 已完成的步骤摘要 */}
      {completedCount > 0 && (
        <div style={{ marginTop: 12, paddingTop: 8, borderTop: "1px solid #f0f0f0" }}>
          {steps
            .filter((s) => s.status === "completed")
            .slice(-3)
            .map((step, idx) => (
              <div key={idx} style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 2 }}>
                <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 12 }} />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {toolNameMap[step.toolName] || step.toolName}
                </Text>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

export default ChatSidebar;
