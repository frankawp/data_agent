"use client";

import { useState, useEffect, useCallback } from "react";
import { Menu, Spin, Typography, Empty, theme, Badge, Upload, message, Popconfirm, Button } from "antd";
import {
  TableOutlined,
  DatabaseOutlined,
  EyeOutlined,
  ReloadOutlined,
  UploadOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  DeleteOutlined,
  InboxOutlined,
} from "@ant-design/icons";
import type { MenuProps, UploadProps } from "antd";
import { useWorkspace } from "@/hooks/useWorkspaceContext";
import { useSession } from "@/providers/SessionProvider";

const { Text, Title } = Typography;

interface TableInfo {
  name: string;
  type: "table" | "view";
}

interface ImportFile {
  name: string;
  path: string;
  size: number;
  modified: string;
  type: string;
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// 获取文件图标
function getFileIcon(filename: string, token: { colorSuccess: string }) {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  if (ext === "csv") {
    return <FileTextOutlined style={{ color: token.colorSuccess }} />;
  }
  return <FileExcelOutlined style={{ color: token.colorSuccess }} />;
}

export function Sidebar() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [importFiles, setImportFiles] = useState<ImportFile[]>([]);
  const [importLoading, setImportLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const { setSecondaryContent, setActiveTab } = useWorkspace();
  const { sessionId } = useSession();
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

  // 加载导入文件列表
  const loadImportFiles = useCallback(async () => {
    setImportLoading(true);
    try {
      const url = sessionId
        ? `/api/files/imports?session_id=${sessionId}`
        : "/api/files/imports";
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setImportFiles(data.files || []);
      }
    } catch {
      // 静默处理错误
    } finally {
      setImportLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadTables();
    loadImportFiles();
  }, [loadImportFiles]);

  const handleTableClick = (tableName: string) => {
    setSecondaryContent({
      type: "table",
      data: { tableName },
    });
    setActiveTab("secondary");
  };

  // 删除导入文件
  const handleDeleteImport = async (file: ImportFile, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const url = sessionId
        ? `/api/files/imports/${file.name}?session_id=${sessionId}`
        : `/api/files/imports/${file.name}`;
      const res = await fetch(url, { method: "DELETE" });
      if (res.ok) {
        message.success(`${file.name} 已删除`);
        loadImportFiles();
      } else {
        throw new Error("删除失败");
      }
    } catch {
      message.error("删除失败");
    }
  };

  // 上传配置
  const uploadProps: UploadProps = {
    name: "file",
    multiple: true,
    action: sessionId
      ? `/api/files/upload?session_id=${sessionId}`
      : "/api/files/upload",
    accept: ".xlsx,.xls,.csv",
    showUploadList: false,
    beforeUpload: (file) => {
      const isValidType =
        file.type === "text/csv" ||
        file.type === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
        file.type === "application/vnd.ms-excel" ||
        file.name.endsWith(".csv") ||
        file.name.endsWith(".xlsx") ||
        file.name.endsWith(".xls");

      if (!isValidType) {
        message.error("只支持 Excel 和 CSV 文件");
        return false;
      }

      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error("文件不能超过 50MB");
        return false;
      }

      return true;
    },
    onChange: (info) => {
      const { status } = info.file;
      if (status === "uploading") {
        setUploading(true);
      }
      if (status === "done") {
        setUploading(false);
        message.success(`${info.file.name} 上传成功`);
        loadImportFiles();
      } else if (status === "error") {
        setUploading(false);
        message.error(`${info.file.name} 上传失败`);
      }
    },
  };

  // 构建菜单项
  const menuItems: MenuProps["items"] = [
    // 数据库浏览器
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
    // 导入文件
    {
      key: "imports",
      icon: <UploadOutlined style={{ color: token.colorPrimary }} />,
      label: (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span style={{ fontWeight: 500 }}>导入文件</span>
          <Badge
            count={importFiles.length}
            showZero
            style={{
              backgroundColor: token.colorFillSecondary,
              color: token.colorTextSecondary,
              fontSize: 11,
            }}
          />
        </div>
      ),
      children: [
        // 上传按钮
        {
          key: "upload",
          label: (
            <Upload {...uploadProps}>
              <div
                style={{
                  padding: `${token.paddingSM}px`,
                  textAlign: "center",
                  border: `1px dashed ${token.colorBorder}`,
                  borderRadius: token.borderRadius,
                  cursor: "pointer",
                  background: token.colorBgTextHover,
                }}
              >
                {uploading ? (
                  <Spin size="small" />
                ) : (
                  <>
                    <InboxOutlined style={{ fontSize: 20, color: token.colorPrimary }} />
                    <div style={{ fontSize: 12, color: token.colorTextSecondary, marginTop: 4 }}>
                      点击或拖拽上传
                    </div>
                  </>
                )}
              </div>
            </Upload>
          ),
          disabled: true,
        },
        // 文件列表
        ...(importLoading
          ? [
              {
                key: "import-loading",
                label: (
                  <div style={{ padding: `${token.paddingSM}px 0`, textAlign: "center" }}>
                    <Spin size="small" />
                  </div>
                ),
                disabled: true,
              },
            ]
          : importFiles.length === 0
            ? [
                {
                  key: "import-empty",
                  label: (
                    <Text type="secondary" style={{ fontSize: 12, display: "block", textAlign: "center", padding: `${token.paddingSM}px 0` }}>
                      暂无文件
                    </Text>
                  ),
                  disabled: true,
                },
              ]
            : importFiles.map((file) => ({
                key: `import-${file.name}`,
                icon: getFileIcon(file.name, token),
                label: (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      width: "100%",
                      minWidth: 0,
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 0, overflow: "hidden" }}>
                      <div
                        style={{
                          fontSize: 13,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          lineHeight: 1.4,
                        }}
                        title={file.name}
                      >
                        {file.name}
                      </div>
                      <Text type="secondary" style={{ fontSize: 11, lineHeight: 1.2 }}>
                        {formatSize(file.size)}
                      </Text>
                    </div>
                    <Popconfirm
                      title="确定删除？"
                      onConfirm={(e) => handleDeleteImport(file, e as unknown as React.MouseEvent)}
                      onCancel={(e) => e?.stopPropagation()}
                      okText="删除"
                      cancelText="取消"
                    >
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={(e) => e.stopPropagation()}
                        style={{ marginLeft: 8, flexShrink: 0 }}
                      />
                    </Popconfirm>
                  </div>
                ),
              }))),
      ],
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
          onClick={() => {
            loadTables();
            loadImportFiles();
          }}
          spin={loading || importLoading}
          style={{
            cursor: "pointer",
            color: token.colorTextSecondary,
            fontSize: 14,
            transition: "color 0.2s",
          }}
        />
      </div>

      {/* 菜单区域 */}
      <div
        style={{ flex: 1, overflow: "auto", padding: `${token.paddingSM}px 0` }}
        className="sidebar-menu-container"
      >
        <style>{`
          .sidebar-menu-container .ant-menu-item {
            height: auto !important;
            line-height: 1.4 !important;
            padding-top: 8px !important;
            padding-bottom: 8px !important;
          }
          .sidebar-menu-container .ant-menu-submenu-title {
            height: auto !important;
            line-height: 1.4 !important;
          }
        `}</style>
        <Menu
          mode="inline"
          defaultOpenKeys={[]}
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
