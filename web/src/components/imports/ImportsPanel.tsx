"use client";

/**
 * 导入文件面板
 *
 * 支持上传 Excel/CSV 文件，显示当前会话的导入文件列表，支持预览和删除。
 */

import { useState, useEffect, useCallback } from "react";
import {
  List,
  Button,
  Empty,
  Spin,
  Typography,
  Space,
  Tag,
  Card,
  message,
  Popconfirm,
  Upload,
  Table,
} from "antd";
import type { UploadProps } from "antd";
import {
  ReloadOutlined,
  UploadOutlined,
  DeleteOutlined,
  CloseOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  InboxOutlined,
} from "@ant-design/icons";
import { useSession } from "@/providers/SessionProvider";

const { Text, Title } = Typography;
const { Dragger } = Upload;

// 文件类型
interface ImportFile {
  name: string;
  path: string;
  size: number;
  modified: number;
  type: string;
}

// 预览内容
interface PreviewContent {
  type: string;
  filename: string;
  columns: string[];
  data: Record<string, unknown>[];
  preview_rows: number;
  total_rows: number;
  sheets?: string[];
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// 格式化时间
function formatTime(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// 获取文件图标
function getFileIcon(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const iconMap: Record<string, React.ReactNode> = {
    csv: <FileTextOutlined style={{ color: "#52c41a" }} />,
    xlsx: <FileExcelOutlined style={{ color: "#52c41a" }} />,
    xls: <FileExcelOutlined style={{ color: "#52c41a" }} />,
  };
  return iconMap[ext] || <FileTextOutlined />;
}

// 获取文件类型标签
function getFileTypeLabel(filename: string): { label: string; color: string } {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const typeMap: Record<string, { label: string; color: string }> = {
    csv: { label: "CSV", color: "green" },
    xlsx: { label: "Excel", color: "green" },
    xls: { label: "Excel", color: "green" },
  };
  return typeMap[ext] || { label: ext.toUpperCase(), color: "default" };
}

export function ImportsPanel() {
  const { sessionId } = useSession();
  const [files, setFiles] = useState<ImportFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<ImportFile | null>(null);
  const [preview, setPreview] = useState<PreviewContent | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  // 获取导入文件列表
  const fetchImports = useCallback(async () => {
    setLoading(true);

    try {
      const url = sessionId
        ? `/api/files/imports?session_id=${sessionId}`
        : "/api/files/imports";
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error("获取导入文件失败");
      }
      const data = await res.json();
      setFiles(data.files || []);
    } catch (err) {
      message.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchImports();
  }, [fetchImports]);

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
        file.type ===
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
        file.type === "application/vnd.ms-excel" ||
        file.name.endsWith(".csv") ||
        file.name.endsWith(".xlsx") ||
        file.name.endsWith(".xls");

      if (!isValidType) {
        message.error("只支持 Excel (.xlsx, .xls) 和 CSV (.csv) 文件");
        return false;
      }

      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error("文件大小不能超过 50MB");
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
        fetchImports();
      } else if (status === "error") {
        setUploading(false);
        message.error(`${info.file.name} 上传失败`);
      }
    },
  };

  // 预览文件
  const handlePreview = async (file: ImportFile) => {
    setSelectedFile(file);
    setPreviewLoading(true);
    setPreview(null);

    try {
      const url = sessionId
        ? `/api/files/imports/${file.name}/preview?session_id=${sessionId}`
        : `/api/files/imports/${file.name}/preview`;
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error("预览失败");
      }
      const data = await res.json();
      setPreview(data);
    } catch (err) {
      message.error(`预览失败: ${(err as Error).message}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  // 删除文件
  const handleDelete = async (file: ImportFile) => {
    try {
      const url = sessionId
        ? `/api/files/imports/${file.name}?session_id=${sessionId}`
        : `/api/files/imports/${file.name}`;
      const res = await fetch(url, { method: "DELETE" });
      if (!res.ok) {
        throw new Error("删除失败");
      }
      message.success(`${file.name} 已删除`);
      if (selectedFile?.name === file.name) {
        setSelectedFile(null);
        setPreview(null);
      }
      fetchImports();
    } catch (err) {
      message.error((err as Error).message);
    }
  };

  // 生成预览表格列
  const previewColumns = preview?.columns.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
    width: 120,
  }));

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "#fff",
      }}
    >
      {/* 头部 */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 16px",
          borderBottom: "1px solid #f0f0f0",
        }}
      >
        <div>
          <Title
            level={5}
            style={{ margin: 0, display: "flex", alignItems: "center", gap: 8 }}
          >
            <UploadOutlined /> 导入文件
          </Title>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {loading ? "加载中..." : `${files.length} 个文件`}
          </Text>
        </div>
        <Button
          type="text"
          icon={<ReloadOutlined spin={loading} />}
          onClick={fetchImports}
          disabled={loading}
        />
      </div>

      {/* 上传区域 */}
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #f0f0f0" }}>
        <Dragger {...uploadProps} style={{ padding: "8px 0" }}>
          <p className="ant-upload-drag-icon" style={{ marginBottom: 8 }}>
            <InboxOutlined style={{ fontSize: 32, color: "#1890ff" }} />
          </p>
          <p
            className="ant-upload-text"
            style={{ fontSize: 14, marginBottom: 4 }}
          >
            点击或拖拽文件到此区域上传
          </p>
          <p
            className="ant-upload-hint"
            style={{ fontSize: 12, color: "#999" }}
          >
            支持 Excel (.xlsx, .xls) 和 CSV (.csv) 文件，最大 50MB
          </p>
        </Dragger>
      </div>

      {/* 文件列表 */}
      <div style={{ flex: 1, overflow: "auto" }}>
        {files.length === 0 && !loading ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span>
                暂无导入文件
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  上传 Excel 或 CSV 文件开始分析
                </Text>
              </span>
            }
            style={{ marginTop: 24 }}
          />
        ) : (
          <List
            loading={loading || uploading}
            dataSource={files}
            renderItem={(file) => (
              <List.Item
                style={{
                  padding: "12px 16px",
                  cursor: "pointer",
                  background:
                    selectedFile?.name === file.name ? "#e6f4ff" : "transparent",
                }}
                onClick={() => handlePreview(file)}
                actions={[
                  <Popconfirm
                    key="delete"
                    title="确定删除此文件？"
                    onConfirm={(e) => {
                      e?.stopPropagation();
                      handleDelete(file);
                    }}
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
                    />
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <span style={{ fontSize: 20 }}>{getFileIcon(file.name)}</span>
                  }
                  title={
                    <Text ellipsis style={{ maxWidth: 180 }}>
                      {file.name}
                    </Text>
                  }
                  description={
                    <Space size={4}>
                      <Tag
                        color={getFileTypeLabel(file.name).color}
                        style={{ marginRight: 0 }}
                      >
                        {getFileTypeLabel(file.name).label}
                      </Tag>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatSize(file.size)}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatTime(file.modified)}
                      </Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </div>

      {/* 预览区域 */}
      {selectedFile && (
        <Card
          size="small"
          title={
            <Space>
              <Text ellipsis style={{ maxWidth: 150 }}>
                预览: {selectedFile.name}
              </Text>
              {preview && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  ({preview.preview_rows}/{preview.total_rows} 行)
                </Text>
              )}
            </Space>
          }
          extra={
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={() => {
                setSelectedFile(null);
                setPreview(null);
              }}
            />
          }
          style={{
            borderRadius: 0,
            borderLeft: 0,
            borderRight: 0,
            borderBottom: 0,
          }}
          styles={{ body: { padding: 0 } }}
        >
          <div style={{ maxHeight: 250, overflow: "auto" }}>
            {previewLoading ? (
              <div style={{ textAlign: "center", padding: "20px 0" }}>
                <Spin size="small" />
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  加载中...
                </Text>
              </div>
            ) : preview ? (
              <Table
                columns={previewColumns}
                dataSource={preview.data.map((row, i) => ({
                  key: i,
                  ...row,
                }))}
                size="small"
                pagination={false}
                scroll={{ x: "max-content" }}
                style={{ fontSize: 12 }}
              />
            ) : null}
          </div>
          {preview?.sheets && preview.sheets.length > 1 && (
            <div style={{ padding: "8px 12px", background: "#fafafa" }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                工作表: {preview.sheets.join(", ")}
              </Text>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

export default ImportsPanel;
