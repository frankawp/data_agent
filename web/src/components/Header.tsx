"use client";

import { useState } from "react";
import { Layout, Space, Button, Badge, Dropdown, Card, Typography, Modal } from "antd";
import { SettingOutlined, PlusOutlined, CloseOutlined } from "@ant-design/icons";
import { ModeControl } from "./modes/ModeControl";
import { useSession } from "@/providers/SessionProvider";

const { Header: AntHeader } = Layout;
const { Text } = Typography;

export function Header() {
  const { sessionId, resetSession, isLoading } = useSession();
  const [showModes, setShowModes] = useState(false);

  const handleNewSession = async () => {
    Modal.confirm({
      title: "确定要开启新会话吗？",
      content: "当前会话的数据将被保留，但您将切换到一个全新的会话。",
      okText: "确定",
      cancelText: "取消",
      onOk: async () => {
        await resetSession();
        window.location.reload();
      },
    });
  };

  // 模式设置下拉面板内容
  const modeDropdownContent = (
    <Card
      title={
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>模式设置</span>
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={() => setShowModes(false)}
          />
        </div>
      }
      style={{ width: 320 }}
      styles={{ header: { borderBottom: "1px solid #f0f0f0" }, body: { padding: 16 } }}
    >
      <ModeControl />
    </Card>
  );

  return (
    <AntHeader
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 16px",
        borderBottom: "1px solid #f0f0f0",
        height: 56,
        lineHeight: "56px",
      }}
    >
      {/* Logo 和标题 */}
      <Space size="middle">
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "#2563eb",
            color: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "bold",
            fontSize: 14,
          }}
        >
          DA
        </div>
        <Text strong style={{ fontSize: 18 }}>
          Data Agent
        </Text>
      </Space>

      {/* 右侧操作区 */}
      <Space size="large">
        {/* 会话信息 */}
        {sessionId && (
          <Space>
            <Text type="secondary" style={{ fontSize: 14 }}>
              会话: {sessionId.slice(-8)}
            </Text>
            <Button
              size="small"
              type="link"
              icon={<PlusOutlined />}
              onClick={handleNewSession}
              loading={isLoading}
            >
              新建
            </Button>
          </Space>
        )}

        {/* 数据库状态 */}
        <Badge status="success" text="已连接" />

        {/* 模式设置按钮 */}
        <Dropdown
          open={showModes}
          onOpenChange={setShowModes}
          popupRender={() => modeDropdownContent}
          trigger={["click"]}
          placement="bottomRight"
        >
          <Button icon={<SettingOutlined />}>模式设置</Button>
        </Dropdown>
      </Space>
    </AntHeader>
  );
}
