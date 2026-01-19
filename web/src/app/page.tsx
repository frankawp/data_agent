"use client";

import { Layout, theme } from "antd";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { Workspace } from "@/components/workspace/Workspace";
import { Header } from "@/components/Header";
import { WorkspaceProvider } from "@/hooks/useWorkspaceContext";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { SessionProvider } from "@/providers/SessionProvider";

const { Sider, Content } = Layout;

export default function Home() {
  const { token } = theme.useToken();

  return (
    <SessionProvider>
      <WorkspaceProvider>
        <Layout
          style={{
            height: "100vh",
            background: token.colorBgLayout,
          }}
        >
          {/* 顶部导航 */}
          <Header />

          <Layout style={{ background: "transparent" }}>
            {/* 左侧数据库浏览器 */}
            <Sider
              width={256}
              style={{
                background: token.colorBgContainer,
                borderRight: `1px solid ${token.colorBorderSecondary}`,
                transition: "all 0.25s ease",
              }}
            >
              <Sidebar />
            </Sider>

            {/* 主工作区 */}
            <Content
              style={{
                overflow: "hidden",
                background: token.colorBgLayout,
                transition: "background 0.25s ease",
              }}
            >
              <Workspace />
            </Content>

            {/* 右侧聊天面板 */}
            <Sider
              width={400}
              style={{
                background: token.colorBgContainer,
                borderLeft: `1px solid ${token.colorBorderSecondary}`,
                transition: "all 0.25s ease",
              }}
            >
              <ChatSidebar />
            </Sider>
          </Layout>
        </Layout>
      </WorkspaceProvider>
    </SessionProvider>
  );
}
