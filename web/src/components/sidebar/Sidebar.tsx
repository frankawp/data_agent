"use client";

import { useState, useEffect } from "react";
import { Menu, Spin, Typography, Empty, theme, Badge } from "antd";
import {
  TableOutlined,
  DatabaseOutlined,
  EyeOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import type { MenuProps } from "antd";
import { useWorkspace } from "@/hooks/useWorkspaceContext";

const { Text, Title } = Typography;

interface TableInfo {
  name: string;
  type: "table" | "view";
}

export function Sidebar() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const { setSecondaryContent, setActiveTab } = useWorkspace();
  const { token } = theme.useToken();

  // 加载数据库表
  const loadTables = () => {
    setLoading(true);
    fetch("/api/database/tables")
      .then((r) => r.json())
      .then((data) => {
        if (data.tables) {
          const tableList: TableInfo[] = [];
          if (typeof data.tables === "string") {
            const lines = data.tables.split("\n");
            lines.forEach((line: string) => {
              const trimmed = line.trim();
              if (trimmed && trimmed.startsWith("- ")) {
                const name = trimmed.slice(2);
                tableList.push({ name, type: "table" });
              }
            });
          }
          setTables(tableList);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTables();
  }, []);

  const handleTableClick = (tableName: string) => {
    setSecondaryContent({
      type: "table",
      data: { tableName },
    });
    setActiveTab("secondary");
  };

  // 构建菜单项
  const menuItems: MenuProps["items"] = [
    {
      key: "database",
      icon: <DatabaseOutlined style={{ color: token.colorPrimary }} />,
      label: (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span style={{ fontWeight: 500 }}>数据库浏览器</span>
          <Badge
            count={tables.length}
            showZero
            style={{
              backgroundColor: token.colorFillSecondary,
              color: token.colorTextSecondary,
              fontSize: 11,
            }}
          />
        </div>
      ),
      children: loading
        ? [
            {
              key: "loading",
              label: (
                <div
                  style={{
                    padding: `${token.paddingLG}px 0`,
                    textAlign: "center",
                  }}
                >
                  <Spin size="small" />
                  <Text
                    type="secondary"
                    style={{ display: "block", marginTop: token.marginSM, fontSize: 12 }}
                  >
                    加载表列表...
                  </Text>
                </div>
              ),
              disabled: true,
            },
          ]
        : tables.length === 0
          ? [
              {
                key: "empty",
                label: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        未连接数据库
                      </Text>
                    }
                    style={{ padding: `${token.paddingLG}px 0` }}
                  />
                ),
                disabled: true,
              },
            ]
          : tables.map((table) => ({
              key: table.name,
              icon:
                table.type === "view" ? (
                  <EyeOutlined style={{ color: token.colorWarning }} />
                ) : (
                  <TableOutlined style={{ color: token.colorSuccess }} />
                ),
              label: (
                <span
                  style={{
                    fontSize: 13,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {table.name}
                </span>
              ),
              onClick: () => handleTableClick(table.name),
            })),
    },
  ];

  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* 标题栏 */}
      <div
        style={{
          padding: `${token.paddingSM}px ${token.padding}px`,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Title level={5} style={{ margin: 0, fontSize: 14, fontWeight: 500 }}>
          数据源
        </Title>
        <ReloadOutlined
          onClick={loadTables}
          spin={loading}
          style={{
            cursor: "pointer",
            color: token.colorTextSecondary,
            fontSize: 14,
            transition: "color 0.2s",
          }}
        />
      </div>

      {/* 菜单区域 */}
      <div style={{ flex: 1, overflow: "auto", padding: `${token.paddingSM}px 0` }}>
        <Menu
          mode="inline"
          defaultOpenKeys={["database"]}
          items={menuItems}
          style={{
            border: "none",
            background: "transparent",
          }}
        />
      </div>
    </div>
  );
}
