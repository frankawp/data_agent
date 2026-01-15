"use client";

import { useState } from "react";
import { ModeControl } from "./modes/ModeControl";
import { useSession } from "@/providers/SessionProvider";

export function Header() {
  const { sessionId, resetSession, isLoading } = useSession();
  const [showModes, setShowModes] = useState(false);

  const handleNewSession = async () => {
    if (confirm("确定要开启新会话吗？当前会话的数据将被保留，但您将切换到一个全新的会话。")) {
      await resetSession();
      window.location.reload();
    }
  };

  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-4">
      {/* Logo 和标题 */}
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold">
          DA
        </div>
        <h1 className="text-lg font-semibold text-gray-900">Data Agent</h1>
      </div>

      {/* 会话信息 */}
      <div className="flex items-center gap-4">
        {sessionId && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">
              会话: {sessionId.slice(-8)}
            </span>
            <button
              onClick={handleNewSession}
              disabled={isLoading}
              className="rounded px-2 py-0.5 text-xs text-blue-600 hover:bg-blue-50 disabled:opacity-50"
              title="开启新会话"
            >
              新建
            </button>
          </div>
        )}

        {/* 数据库状态 */}
        <div className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-green-500"></span>
          <span className="text-sm text-gray-600">已连接</span>
        </div>

        {/* 模式设置按钮 */}
        <button
          onClick={() => setShowModes(!showModes)}
          className="rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50"
        >
          模式设置
        </button>
      </div>

      {/* 模式设置面板 */}
      {showModes && (
        <div className="absolute right-4 top-14 z-50 w-80 rounded-lg border bg-white p-4 shadow-lg">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-medium">模式设置</h3>
            <button
              onClick={() => setShowModes(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <ModeControl />
        </div>
      )}
    </header>
  );
}
