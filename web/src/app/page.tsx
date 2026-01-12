"use client";

import { Sidebar } from "@/components/sidebar/Sidebar";
import { Workspace } from "@/components/workspace/Workspace";
import { Header } from "@/components/Header";
import { WorkspaceProvider } from "@/hooks/useWorkspaceContext";
import { ChatSidebar } from "@/components/chat/ChatSidebar";

export default function Home() {
  return (
    <WorkspaceProvider>
      <div className="flex h-screen flex-col bg-gray-50">
        {/* Header */}
        <Header />

        {/* Main Content */}
        <div className="flex flex-1 overflow-hidden">
          {/* 左侧边栏 */}
          <Sidebar className="w-64 border-r bg-white" />

          {/* 主/副工作区 */}
          <main className="flex-1 overflow-hidden">
            <Workspace />
          </main>

          {/* 聊天侧边栏 - AI 对话 */}
          <ChatSidebar className="w-96" />
        </div>
      </div>
    </WorkspaceProvider>
  );
}
