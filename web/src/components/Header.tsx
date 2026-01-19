"use client";

import { useState } from "react";
import {
  Layout,
  Space,
  Button,
  Badge,
  Dropdown,
  Card,
  Typography,
  Modal,
  Tooltip,
  theme,
  Segmented,
} from "antd";
import {
  SettingOutlined,
  PlusOutlined,
  CloseOutlined,
  SunOutlined,
  MoonOutlined,
  DesktopOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { ModeControl } from "./modes/ModeControl";
import { useSession } from "@/providers/SessionProvider";
import { useTheme } from "@/providers/ThemeProvider";

const { Header: AntHeader } = Layout;
const { Text } = Typography;

export function Header() {
  const { sessionId, resetSession, isLoading } = useSession();
  const { mode, setMode, isDark } = useTheme();
  const { token } = theme.useToken();
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

  // 主题选项
  const themeOptions = [
    { label: <SunOutlined />, value: "light" },
    { label: <DesktopOutlined />, value: "system" },
    { label: <MoonOutlined />, value: "dark" },
  ];

  // 模式设置下拉面板内容
  const modeDropdownContent = (
    <Card
      title={
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>模式设置</span>
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={() => setShowModes(false)}
          />
        </div>
      }
      style={{
        width: 320,
        boxShadow: token.boxShadowSecondary,
        border: `1px solid ${token.colorBorderSecondary}`,
      }}
      styles={{
        header: { borderBottom: `1px solid ${token.colorBorderSecondary}` },
        body: { padding: token.padding },
      }}
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
        padding: `0 ${token.paddingLG}px`,
        borderBottom: `1px solid ${token.colorBorderSecondary}`,
        height: 56,
        lineHeight: "56px",
        background: token.colorBgContainer,
        transition: "all 0.25s ease",
      }}
    >
      {/* Logo 和标题 */}
      <Space size="middle" align="center">
        <div
          className="gradient-primary"
          style={{
            width: 36,
            height: 36,
            borderRadius: token.borderRadiusLG,
            color: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "bold",
            fontSize: 14,
            boxShadow: "0 2px 8px rgba(37, 99, 235, 0.3)",
          }}
        >
          DA
        </div>
        <div>
          <Text strong style={{ fontSize: 18, display: "block", lineHeight: 1.2 }}>
            Data Agent
          </Text>
          <Text type="secondary" style={{ fontSize: 12, lineHeight: 1 }}>
            智能数据分析助手
          </Text>
        </div>
      </Space>

      {/* 右侧操作区 */}
      <Space size="middle">
        {/* 会话信息 */}
        {sessionId && (
          <Space
            style={{
              background: token.colorFillTertiary,
              padding: `${token.paddingXS}px ${token.paddingSM}px`,
              borderRadius: token.borderRadius,
            }}
          >
            <Text type="secondary" style={{ fontSize: 13 }}>
              会话: <code style={{ fontFamily: "var(--font-geist-mono)" }}>{sessionId.slice(-8)}</code>
            </Text>
            <Tooltip title="新建会话">
              <Button
                size="small"
                type="text"
                icon={<PlusOutlined />}
                onClick={handleNewSession}
                loading={isLoading}
              />
            </Tooltip>
          </Space>
        )}

        {/* 数据库状态 */}
        <Tooltip title="数据库连接状态">
          <Badge
            status="success"
            text={
              <Space size={4}>
                <DatabaseOutlined style={{ color: token.colorTextSecondary }} />
                <Text type="secondary" style={{ fontSize: 13 }}>
                  已连接
                </Text>
              </Space>
            }
          />
        </Tooltip>

        {/* 主题切换 */}
        <Tooltip title="主题模式">
          <Segmented
            value={mode}
            onChange={(value) => setMode(value as "light" | "dark" | "system")}
            options={themeOptions}
            size="small"
          />
        </Tooltip>

        {/* 模式设置按钮 */}
        <Dropdown
          open={showModes}
          onOpenChange={setShowModes}
          popupRender={() => modeDropdownContent}
          trigger={["click"]}
          placement="bottomRight"
        >
          <Button
            icon={<SettingOutlined />}
            style={{
              borderRadius: token.borderRadius,
            }}
          >
            模式设置
          </Button>
        </Dropdown>
      </Space>
    </AntHeader>
  );
}
