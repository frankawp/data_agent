"use client";

import { useState, useEffect } from "react";
import { Menu, Spin, Typography } from "antd";
import { TableOutlined, DatabaseOutlined, EyeOutlined } from "@ant-design/icons";
import type { MenuProps } from "antd";
import { useWorkspace } from "@/hooks/useWorkspaceContext";

const { Text } = Typography;

interface TableInfo {
  name: string;
  type: "table" | "view";
}

export function Sidebar() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const { setSecondaryContent, setActiveTab } = useWorkspace();

  // 加载数据库表
  useEffect(() => {
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
      icon: <DatabaseOutlined />,
      label: "数据库浏览器",
      children: loading
        ? [
            {
              key: "loading",
              label: (
                <div style={{ padding: "8px 0", textAlign: "center" }}>
                  <Spin size="small" />
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
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    未连接数据库
                  </Text>
                ),
                disabled: true,
              },
            ]
          : tables.map((table) => ({
              key: table.name,
              icon: table.type === "view" ? <EyeOutlined /> : <TableOutlined />,
              label: table.name,
              onClick: () => handleTableClick(table.name),
            })),
    },
  ];

  return (
    <div style={{ height: "100%", overflow: "auto", paddingTop: 8 }}>
      <Menu
        mode="inline"
        defaultOpenKeys={["database"]}
        items={menuItems}
        style={{ border: "none", background: "transparent" }}
      />
    </div>
  );
}
