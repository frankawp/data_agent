"use client";

import { useState, useEffect } from "react";
import { ModeControl } from "./modes/ModeControl";

interface SessionInfo {
  session_id: string;
  export_dir: string;
}

export function Header() {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [showModes, setShowModes] = useState(false);

  useEffect(() => {
    // 获取会话信息
    fetch("/api/sessions")
      .then((r) => r.json())
      .then(setSessionInfo)
      .catch(() => {});
  }, []);

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
        {sessionInfo && (
          <span className="text-sm text-gray-500">
            会话: {sessionInfo.session_id.slice(-8)}
          </span>
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
