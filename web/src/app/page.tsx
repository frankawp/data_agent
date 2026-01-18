"use client";

import { Layout } from "antd";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { Workspace } from "@/components/workspace/Workspace";
import { Header } from "@/components/Header";
import { WorkspaceProvider } from "@/hooks/useWorkspaceContext";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { SessionProvider } from "@/providers/SessionProvider";

const { Sider, Content } = Layout;

export default function Home() {
  return (
    <SessionProvider>
      <WorkspaceProvider>
        <Layout style={{ height: "100vh" }}>
          {/* 顶部导航 */}
          <Header />

          <Layout>
            {/* 左侧数据库浏览器 */}
            <Sider
              width={256}
              theme="light"
              style={{ borderRight: "1px solid #f0f0f0" }}
            >
              <Sidebar />
            </Sider>

            {/* 主工作区 */}
            <Content style={{ overflow: "hidden" }}>
              <Workspace />
            </Content>

            {/* 右侧聊天面板 */}
            <Sider
              width={384}
              theme="light"
              style={{ borderLeft: "1px solid #f0f0f0" }}
            >
              <ChatSidebar />
            </Sider>
          </Layout>
        </Layout>
      </WorkspaceProvider>
    </SessionProvider>
  );
}
