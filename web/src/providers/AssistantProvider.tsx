"use client";

/**
 * Assistant UI Provider
 *
 * 集成 assistant-ui 库，提供专业的 AI Agent 聊天界面。
 * 支持 tool calls 显示、用户确认、流式中断等功能。
 */

import {
  AssistantRuntimeProvider,
  useExternalStoreRuntime,
  ThreadMessageLike,
  AppendMessage,
} from "@assistant-ui/react";
import { useState, useCallback, useRef, ReactNode } from "react";

// 消息类型
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: Array<{
    id: string;
    name: string;
    args: Record<string, unknown>;
    result?: string;
  }>;
}

// 转换消息格式
function convertMessage(message: Message): ThreadMessageLike {
  return {
    id: message.id,
    role: message.role,
    content: [{ type: "text" as const, text: message.content }],
  };
}

// Provider Props
interface AssistantProviderProps {
  children: ReactNode;
  sessionId?: string;
}

export function AssistantProvider({ children, sessionId }: AssistantProviderProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 发送消息到后端
  const onNew = useCallback(
    async (message: AppendMessage) => {
      // 取消之前的请求
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content:
          typeof message.content === "string"
            ? message.content
            : message.content
                .filter((part) => part.type === "text")
                .map((part) => (part as { type: "text"; text: string }).text)
                .join("\n"),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsRunning(true);

      // 创建新的 AbortController
      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch("/api/chat/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: userMessage.content,
            session_id: sessionId,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 处理 SSE 流
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let assistantContent = "";
        const toolCalls: Message["toolCalls"] = [];

        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: "",
          toolCalls: [],
        };

        setMessages((prev) => [...prev, assistantMessage]);

        while (reader) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let currentEvent = "";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ") && currentEvent) {
              try {
                const data = JSON.parse(line.slice(6));

                switch (currentEvent) {
                  case "tool_call":
                    toolCalls.push({
                      id: `tool-${data.step}`,
                      name: data.tool_name,
                      args: data.args,
                    });
                    break;

                  case "tool_result":
                    const toolCall = toolCalls.find(
                      (t) => t.name === data.tool_name
                    );
                    if (toolCall) {
                      toolCall.result = data.result;
                    }
                    break;

                  case "message":
                    assistantContent = data.content;
                    break;

                  case "done":
                    // 更新最终消息
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === assistantMessage.id
                          ? { ...m, content: assistantContent, toolCalls }
                          : m
                      )
                    );
                    break;
                }
              } catch {
                // 忽略 JSON 解析错误
              }
            }
          }
        }
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          console.error("Chat error:", error);
          setMessages((prev) => [
            ...prev,
            {
              id: `error-${Date.now()}`,
              role: "assistant",
              content: `错误: ${(error as Error).message}`,
            },
          ]);
        }
      } finally {
        setIsRunning(false);
        abortControllerRef.current = null;
      }
    },
    [sessionId]
  );

  // 取消当前请求
  const onCancel = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsRunning(false);
    }
  }, []);

  // 创建 runtime
  const runtime = useExternalStoreRuntime({
    isRunning,
    messages,
    convertMessage,
    onNew,
    onCancel,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}

export default AssistantProvider;
