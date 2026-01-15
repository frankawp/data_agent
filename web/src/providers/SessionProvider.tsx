"use client";

/**
 * 会话 Provider
 *
 * 管理当前会话 ID，在前端组件之间共享会话状态。
 * 确保所有 API 请求使用同一个 session_id，实现会话隔离。
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

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

  // 获取当前会话信息
  const fetchSession = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await fetch("/api/sessions");
      if (!res.ok) {
        throw new Error("获取会话信息失败");
      }
      const data = await res.json();
      setSessionId(data.session_id);
    } catch (err) {
      setError((err as Error).message);
      console.error("Failed to fetch session:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

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
      setSessionId(data.session_id);
    } catch (err) {
      setError((err as Error).message);
      console.error("Failed to reset session:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

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
