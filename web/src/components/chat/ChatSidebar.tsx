"use client";

/**
 * 聊天侧边栏组件
 *
 * 使用 WebSocket 实现双向通信，支持：
 * - AI 工作期间发送用户反馈
 * - 安全模式下 SQL 执行确认
 * - 工具调用显示、流式响应、用户中断
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
  Modal,
  Alert,
  theme,
  Tooltip,
} from "antd";
import {
  SendOutlined,
  ClearOutlined,
  StopOutlined,
  MessageOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  BulbOutlined,
  ExclamationCircleOutlined,
  EditOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  LineChartOutlined,
  FileSearchOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useWorkspace, StreamingStep } from "@/hooks/useWorkspaceContext";
import { useSession } from "@/providers/SessionProvider";

const { TextArea } = Input;
const { Text, Title } = Typography;

// 确认请求类型
interface ConfirmationRequest {
  tool_name: string;
  args: Record<string, unknown>;
  tool_call_id: string;
  description: string;
}

// WebSocket 连接状态
type WSState = "connecting" | "connected" | "disconnected" | "error";

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
      role: "user" | "assistant" | "feedback";
      content: string;
    }>
  >([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [wsState, setWsState] = useState<WSState>("disconnected");
  const [pendingConfirmation, setPendingConfirmation] = useState<ConfirmationRequest | null>(null);
  const [editedArgs, setEditedArgs] = useState<string>("");

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 处理服务端消息 - 必须在 connectWebSocket 之前声明
  const handleServerMessage = useCallback((data: Record<string, unknown>) => {
    const type = data.type as string;

    switch (type) {
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

      case "confirmation_request":
        // 显示确认对话框
        setPendingConfirmation({
          tool_name: data.tool_name as string,
          args: data.args as Record<string, unknown>,
          tool_call_id: data.tool_call_id as string,
          description: data.description as string,
        });
        setEditedArgs(JSON.stringify(data.args, null, 2));
        break;

      case "feedback_ack":
        // 反馈已确认，可以显示小提示
        console.log("Feedback acknowledged:", data.message);
        break;

      case "message":
        // AI 最终回复
        setMessages((prev) => {
          const lastAssistant = [...prev].reverse().find((m) => m.role === "assistant");
          if (lastAssistant && !lastAssistant.content) {
            return prev.map((m) =>
              m.id === lastAssistant.id
                ? { ...m, content: data.content as string }
                : m
            );
          }
          return prev;
        });
        break;

      case "error":
        console.error("Server error:", data.error);
        setMessages((prev) => {
          const lastAssistant = [...prev].reverse().find((m) => m.role === "assistant");
          if (lastAssistant && !lastAssistant.content) {
            return prev.map((m) =>
              m.id === lastAssistant.id
                ? { ...m, content: `错误: ${data.error}` }
                : m
            );
          }
          return prev;
        });
        break;

      case "done":
        finishStreaming();
        setIsProcessing(false);
        break;
    }
  }, [
    addStreamingStep,
    updateStreamingStepResult,
    setCurrentToolResult,
    finishStreaming,
    addSubagentStep,
    updateSubagentStepResult,
  ]);

  // WebSocket 连接管理
  const connectWebSocket = useCallback(() => {
    if (!sessionId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // 清理旧连接
    if (wsRef.current) {
      wsRef.current.close();
    }

    setWsState("connecting");

    // 连接到后端 WebSocket
    // 优先使用环境变量配置的 WebSocket URL
    const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL;
    let wsUrl: string;

    if (wsBaseUrl) {
      // 使用环境变量配置的 URL
      wsUrl = `${wsBaseUrl}/api/ws/chat?session_id=${sessionId}`;
    } else {
      // 本地开发：根据当前页面协议选择 ws 或 wss
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      wsUrl = `${protocol}//localhost:8000/api/ws/chat?session_id=${sessionId}`;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
      setWsState("connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleServerMessage(data);
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setWsState("error");
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setWsState("disconnected");
      wsRef.current = null;
    };
  }, [sessionId, handleServerMessage]);

  // 初始化 WebSocket 连接
  useEffect(() => {
    if (sessionId) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId, connectWebSocket]);

  // 自动重连机制 - 只在断开后重连，不在初始状态触发
  const wasConnectedRef = useRef(false);
  useEffect(() => {
    if (wsState === "connected") {
      wasConnectedRef.current = true;
    }

    // 只在曾经连接过且现在断开的情况下自动重连
    if (wsState === "disconnected" && sessionId && wasConnectedRef.current) {
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log("Attempting to reconnect WebSocket...");
        connectWebSocket();
      }, 5000);
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [wsState, sessionId, connectWebSocket]);

  // 发送 WebSocket 消息
  const sendWSMessage = useCallback((msg: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    } else {
      console.error("WebSocket not connected");
    }
  }, []);

  // 发送用户消息
  const sendMessage = useCallback(() => {
    if (!input.trim()) return;

    const content = input.trim();
    setInput("");

    if (isProcessing) {
      // AI 工作期间，发送反馈
      const feedbackMessage = {
        id: `feedback-${Date.now()}`,
        role: "feedback" as const,
        content: content,
      };
      setMessages((prev) => [...prev, feedbackMessage]);
      sendWSMessage({ type: "feedback", content });
    } else {
      // 新消息
      const userMessage = {
        id: `user-${Date.now()}`,
        role: "user" as const,
        content: content,
      };
      setMessages((prev) => [...prev, userMessage]);

      // 添加空的 AI 回复占位
      const assistantId = `assistant-${Date.now()}`;
      setMessages((prev) => [...prev, { id: assistantId, role: "assistant", content: "" }]);

      setIsProcessing(true);
      startStreaming();

      // 确保 WebSocket 已连接
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        connectWebSocket();
        // 等待连接后再发送
        setTimeout(() => {
          sendWSMessage({ type: "user_message", content });
        }, 500);
      } else {
        sendWSMessage({ type: "user_message", content });
      }
    }
  }, [input, isProcessing, sendWSMessage, startStreaming, connectWebSocket]);

  // 取消执行
  const handleCancel = useCallback(() => {
    sendWSMessage({ type: "cancel" });
    setIsProcessing(false);
    finishStreaming();
  }, [sendWSMessage, finishStreaming]);

  // 处理确认决定
  const handleConfirmationDecision = useCallback((decision: "approve" | "edit" | "reject") => {
    if (!pendingConfirmation) return;

    const decisionMessage: Record<string, unknown> = {
      type: "decision",
      decision,
      tool_call_id: pendingConfirmation.tool_call_id,
    };

    if (decision === "edit") {
      try {
        const parsed = JSON.parse(editedArgs);
        decisionMessage.edited_args = parsed;
      } catch {
        // 解析失败，使用原始参数
        decisionMessage.edited_args = pendingConfirmation.args;
      }
    }

    sendWSMessage(decisionMessage);
    setPendingConfirmation(null);
    setEditedArgs("");
  }, [pendingConfirmation, editedArgs, sendWSMessage]);

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

  // 连接状态指示器
  const renderConnectionStatus = () => {
    const statusConfig = {
      connecting: { color: "gold", text: "连接中..." },
      connected: { color: "green", text: "已连接" },
      disconnected: { color: "default", text: "已断开" },
      error: { color: "red", text: "连接错误" },
    };
    const config = statusConfig[wsState];
    return (
      <Tag color={config.color} style={{ fontSize: 10 }}>
        {config.text}
      </Tag>
    );
  };

  const { token } = theme.useToken();

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: token.colorBgContainer,
        transition: "background 0.25s ease",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: `${token.paddingSM}px ${token.padding}px`,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          background: `linear-gradient(135deg, ${token.colorPrimaryBg}, ${token.colorInfoBg})`,
        }}
      >
        <Space>
          <div
            className="gradient-primary"
            style={{
              width: 36,
              height: 36,
              borderRadius: token.borderRadiusLG,
              color: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 2px 8px rgba(37, 99, 235, 0.3)",
            }}
          >
            <MessageOutlined style={{ fontSize: 18 }} />
          </div>
          <div>
            <Space size={4}>
              <Title level={5} style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
                数据分析助手
              </Title>
              {renderConnectionStatus()}
            </Space>
            <Text type="secondary" style={{ fontSize: 12 }}>
              AI 驱动的智能分析
            </Text>
          </div>
        </Space>
        <Tooltip title="清空对话">
          <Button
            type="text"
            icon={<ClearOutlined />}
            onClick={clearChat}
            style={{ color: token.colorTextSecondary }}
          >
            清空
          </Button>
        </Tooltip>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflow: "auto",
          padding: messages.length > 0 ? token.padding : 0,
        }}
      >
        {messages.length === 0 ? (
          <WelcomeMessage onSuggestionClick={(text) => setInput(text)} />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: token.marginSM }}>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isLoading={isProcessing && message.role === "assistant" && !message.content}
                streamingSteps={streamingSteps}
                isStreaming={isStreaming}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div
        style={{
          borderTop: `1px solid ${token.colorBorderSecondary}`,
          background: token.colorFillTertiary,
          padding: token.padding,
        }}
      >
        {/* 停止按钮 */}
        {isProcessing && (
          <div style={{ textAlign: "center", marginBottom: token.marginSM }}>
            <Button
              danger
              icon={<StopOutlined />}
              onClick={handleCancel}
              style={{ borderRadius: 20, paddingLeft: 16, paddingRight: 16 }}
            >
              停止生成
            </Button>
          </div>
        )}

        {/* 反馈提示 */}
        {isProcessing && (
          <Alert
            message="AI 正在工作中，您可以随时发送意见或建议"
            type="info"
            showIcon
            style={{
              marginBottom: token.marginSM,
              fontSize: 12,
              borderRadius: token.borderRadius,
            }}
          />
        )}

        <Space.Compact style={{ width: "100%" }}>
          <TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isProcessing ? "输入意见或反馈..." : "描述您的数据分析需求..."}
            rows={2}
            style={{
              borderRadius: `${token.borderRadiusLG}px 0 0 ${token.borderRadiusLG}px`,
              resize: "none",
              background: token.colorBgContainer,
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={sendMessage}
            disabled={!input.trim()}
            style={{
              height: "auto",
              borderRadius: `0 ${token.borderRadiusLG}px ${token.borderRadiusLG}px 0`,
              minWidth: 48,
            }}
          />
        </Space.Compact>
        <Text
          type="secondary"
          style={{
            display: "block",
            textAlign: "center",
            marginTop: token.marginSM,
            fontSize: 12,
          }}
        >
          按 Enter 发送，Shift + Enter 换行
        </Text>
      </div>

      {/* 确认对话框 */}
      <Modal
        title={
          <Space>
            <ExclamationCircleOutlined style={{ color: "#faad14" }} />
            <span>操作确认</span>
          </Space>
        }
        open={!!pendingConfirmation}
        onCancel={() => handleConfirmationDecision("reject")}
        footer={[
          <Button key="reject" danger onClick={() => handleConfirmationDecision("reject")}>
            拒绝
          </Button>,
          <Button key="edit" icon={<EditOutlined />} onClick={() => handleConfirmationDecision("edit")}>
            编辑后执行
          </Button>,
          <Button key="approve" type="primary" onClick={() => handleConfirmationDecision("approve")}>
            批准
          </Button>,
        ]}
        width={600}
      >
        {pendingConfirmation && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>操作描述：</Text>
              <pre
                style={{
                  background: "#f5f5f5",
                  padding: 12,
                  borderRadius: 4,
                  whiteSpace: "pre-wrap",
                  marginTop: 8,
                }}
              >
                {pendingConfirmation.description}
              </pre>
            </div>

            <div>
              <Text strong>参数（可编辑）：</Text>
              <TextArea
                value={editedArgs}
                onChange={(e) => setEditedArgs(e.target.value)}
                rows={6}
                style={{
                  fontFamily: "monospace",
                  fontSize: 12,
                  marginTop: 8,
                }}
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

// 欢迎消息
function WelcomeMessage({ onSuggestionClick }: { onSuggestionClick: (text: string) => void }) {
  const { token } = theme.useToken();

  // 功能特性
  const features = [
    { icon: <DatabaseOutlined />, title: "SQL 查询", desc: "智能 SQL 生成与执行" },
    { icon: <LineChartOutlined />, title: "数据分析", desc: "统计分析与可视化" },
    { icon: <FileSearchOutlined />, title: "表结构", desc: "自动探索数据库结构" },
  ];

  // 示例查询
  const suggestions = [
    { icon: <DatabaseOutlined />, text: "分析数据库中的表结构" },
    { icon: <LineChartOutlined />, text: "查询销售数据并生成报表" },
    { icon: <ThunderboltOutlined />, text: "训练一个预测模型" },
  ];

  return (
    <div
      className="animate-fade-in"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        padding: token.paddingLG,
        textAlign: "center",
      }}
    >
      {/* Logo */}
      <div
        className="gradient-primary"
        style={{
          width: 72,
          height: 72,
          borderRadius: 20,
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 36,
          marginBottom: token.marginLG,
          boxShadow: "0 12px 32px rgba(37, 99, 235, 0.35)",
        }}
      >
        <BulbOutlined />
      </div>

      {/* 标题 */}
      <Title level={4} style={{ marginBottom: token.marginXS }}>
        数据分析助手
      </Title>
      <Text type="secondary" style={{ maxWidth: 300, marginBottom: token.marginLG }}>
        我可以帮助您进行数据查询、分析和可视化。描述您的需求，我将自动规划和执行任务。
      </Text>

      {/* 功能特性 */}
      <div
        style={{
          display: "flex",
          gap: token.marginSM,
          marginBottom: token.marginLG,
          flexWrap: "wrap",
          justifyContent: "center",
        }}
      >
        {features.map((f, i) => (
          <div
            key={i}
            style={{
              padding: `${token.paddingSM}px ${token.padding}px`,
              background: token.colorFillTertiary,
              borderRadius: token.borderRadius,
              display: "flex",
              alignItems: "center",
              gap: token.marginXS,
            }}
          >
            <span style={{ color: token.colorPrimary }}>{f.icon}</span>
            <Text style={{ fontSize: 12 }}>{f.title}</Text>
          </div>
        ))}
      </div>

      {/* 示例查询 */}
      <div style={{ width: "100%", maxWidth: 320 }}>
        <Text
          type="secondary"
          style={{
            fontSize: 12,
            display: "block",
            marginBottom: token.marginSM,
            textAlign: "left",
          }}
        >
          试试这些示例:
        </Text>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, width: "100%" }}>
          {suggestions.map((s, i) => (
            <SuggestionButton key={i} icon={s.icon} text={s.text} onClick={() => onSuggestionClick(s.text)} />
          ))}
        </div>
      </div>
    </div>
  );
}

// 建议按钮
function SuggestionButton({ icon, text, onClick }: { icon: React.ReactNode; text: string; onClick: () => void }) {
  const { token } = theme.useToken();

  return (
    <Button
      block
      className="card-hover"
      onClick={onClick}
      style={{
        height: "auto",
        padding: `${token.paddingSM}px ${token.padding}px`,
        textAlign: "left",
        borderRadius: token.borderRadius,
        display: "flex",
        alignItems: "center",
        gap: token.marginSM,
        border: `1px solid ${token.colorBorderSecondary}`,
      }}
    >
      <span style={{ color: token.colorPrimary, fontSize: 14 }}>{icon}</span>
      <Text style={{ fontSize: 13 }}>{text}</Text>
    </Button>
  );
}

// 消息气泡
interface MessageBubbleProps {
  message: { id: string; role: "user" | "assistant" | "feedback"; content: string };
  isLoading: boolean;
  streamingSteps: StreamingStep[];
  isStreaming: boolean;
}

function MessageBubble({ message, isLoading, streamingSteps, isStreaming }: MessageBubbleProps) {
  const { token } = theme.useToken();
  const isUser = message.role === "user";
  const isFeedback = message.role === "feedback";

  // 反馈消息样式
  if (isFeedback) {
    return (
      <div className="animate-fade-in-up" style={{ display: "flex", justifyContent: "flex-end" }}>
        <Card
          size="small"
          style={{
            maxWidth: "85%",
            borderRadius: token.borderRadiusLG,
            background: token.colorWarningBg,
            border: `1px solid ${token.colorWarningBorder}`,
          }}
          styles={{ body: { padding: `${token.paddingXS}px ${token.paddingSM}px` } }}
        >
          <Space size={4}>
            <Tag color="warning" style={{ marginRight: 0 }}>
              反馈
            </Tag>
            <Text style={{ color: token.colorWarning }}>{message.content}</Text>
          </Space>
        </Card>
      </div>
    );
  }

  return (
    <div
      className="animate-fade-in-up"
      style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}
    >
      <Card
        size="small"
        style={{
          maxWidth: "85%",
          borderRadius: token.borderRadiusLG,
          background: isUser ? token.colorPrimary : token.colorBgContainer,
          border: isUser ? "none" : `1px solid ${token.colorBorderSecondary}`,
          boxShadow: isUser ? "0 2px 8px rgba(37, 99, 235, 0.2)" : token.boxShadow,
        }}
        styles={{ body: { padding: `${token.paddingSM}px ${token.padding}px` } }}
      >
        {message.content ? (
          isUser ? (
            // 用户消息 - 纯文本
            <Text style={{ color: "#fff", whiteSpace: "pre-wrap" }}>{message.content}</Text>
          ) : (
            // AI 回复 - Markdown 渲染
            <div style={{ color: token.colorText, fontSize: 14, lineHeight: 1.6 }}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => <p style={{ margin: "4px 0" }}>{children}</p>,
                  ul: ({ children }) => (
                    <ul style={{ margin: "4px 0", paddingLeft: 20 }}>{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol style={{ margin: "4px 0", paddingLeft: 20 }}>{children}</ol>
                  ),
                  li: ({ children }) => <li style={{ margin: "2px 0" }}>{children}</li>,
                  strong: ({ children }) => (
                    <strong style={{ color: token.colorSuccess, fontWeight: 600 }}>
                      {children}
                    </strong>
                  ),
                  code: ({ children, className }) => {
                    if (className) return <code>{children}</code>;
                    return (
                      <code
                        style={{
                          background: token.colorFillTertiary,
                          padding: "1px 4px",
                          borderRadius: 3,
                          fontSize: "0.9em",
                        }}
                      >
                        {children}
                      </code>
                    );
                  },
                  pre: ({ children }) => (
                    <pre
                      style={{
                        background: "#1a1a2e",
                        color: "#e0e0e0",
                        padding: 8,
                        borderRadius: token.borderRadiusSM,
                        overflow: "auto",
                        fontSize: 12,
                        margin: "4px 0",
                      }}
                    >
                      {children}
                    </pre>
                  ),
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: token.colorPrimary }}
                    >
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
  const { token } = theme.useToken();
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
    <div style={{ minWidth: 220 }}>
      {/* 进度指示器 */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: token.marginSM,
        }}
      >
        <Space size={4}>
          <RobotOutlined style={{ color: token.colorPrimary }} />
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
        strokeColor={{
          "0%": token.colorPrimary,
          "100%": "#4f46e5",
        }}
        showInfo={false}
      />

      {/* 当前步骤描述 */}
      {currentStep && (
        <Text
          type="secondary"
          style={{ fontSize: 12, display: "block", marginTop: token.marginSM }}
        >
          {getStepDescription(currentStep)}
        </Text>
      )}

      {/* 已完成的步骤摘要 */}
      {completedCount > 0 && (
        <div
          style={{
            marginTop: token.marginSM,
            paddingTop: token.paddingSM,
            borderTop: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          {steps
            .filter((s) => s.status === "completed")
            .slice(-3)
            .map((step, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  marginBottom: 2,
                }}
              >
                <CheckCircleOutlined style={{ color: token.colorSuccess, fontSize: 12 }} />
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
