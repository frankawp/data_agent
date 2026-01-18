"use client";

/**
 * 会话 Provider
 *
 * 管理当前会话 ID，在前端组件之间共享会话状态。
 * 确保所有 API 请求使用同一个 session_id，实现会话隔离。
 *
 * 会话 ID 持久化到 localStorage，确保页面刷新后仍然使用同一个会话。
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

const SESSION_STORAGE_KEY = "data_agent_session_id";

interface SessionContextType {
  sessionId: string | null;
  isLoading: boolean;
  error: string | null;
  refreshSession: () => Promise<void>;
  resetSession: () => Promise<void>;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

interface SessionProviderProps {
  children: ReactNode;
}

export function SessionProvider({ children }: SessionProviderProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 保存 session_id 到 localStorage
  const saveSessionId = useCallback((id: string) => {
    setSessionId(id);
    if (typeof window !== "undefined") {
      localStorage.setItem(SESSION_STORAGE_KEY, id);
    }
  }, []);

  // 获取当前会话信息
  // 如果 localStorage 有保存的 session_id，优先使用它
  const fetchSession = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // 先检查 localStorage 中是否有保存的 session_id
      const savedSessionId = typeof window !== "undefined"
        ? localStorage.getItem(SESSION_STORAGE_KEY)
        : null;

      if (savedSessionId) {
        // 验证保存的会话是否仍然有效（目录是否存在）
        const checkRes = await fetch(`/api/sessions/exports?session_id=${savedSessionId}`);
        if (checkRes.ok) {
          // 会话有效，继续使用
          setSessionId(savedSessionId);
          return;
        }
        // 会话无效，清除保存的 ID
        localStorage.removeItem(SESSION_STORAGE_KEY);
      }

      // 没有保存的会话或会话无效，从后端获取当前会话
      const res = await fetch("/api/sessions");
      if (!res.ok) {
        throw new Error("获取会话信息失败");
      }
      const data = await res.json();
      saveSessionId(data.session_id);
    } catch (err) {
      setError((err as Error).message);
      console.error("Failed to fetch session:", err);
    } finally {
      setIsLoading(false);
    }
  }, [saveSessionId]);

  // 重置会话（创建新会话）
  const resetSession = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await fetch("/api/sessions/new", { method: "POST" });
      if (!res.ok) {
        throw new Error("创建新会话失败");
      }
      const data = await res.json();
      saveSessionId(data.session_id);
    } catch (err) {
      setError((err as Error).message);
      console.error("Failed to reset session:", err);
    } finally {
      setIsLoading(false);
    }
  }, [saveSessionId]);

  // 刷新会话信息
  const refreshSession = useCallback(async () => {
    await fetchSession();
  }, [fetchSession]);

  // 初始化时获取会话
  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        isLoading,
        error,
        refreshSession,
        resetSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

// Hook 用于获取会话上下文
export function useSession(): SessionContextType {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return context;
}

export default SessionProvider;
