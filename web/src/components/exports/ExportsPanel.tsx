"use client";

/**
 * 导出文件面板
 *
 * 显示当前会话的所有导出文件，支持预览和下载。
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
  Image,
  Alert,
  Tooltip,
} from "antd";
import {
  ReloadOutlined,
  DownloadOutlined,
  CloseOutlined,
  FileExcelOutlined,
  FileImageOutlined,
  FileTextOutlined,
  CodeOutlined,
  DatabaseOutlined,
  FileOutlined,
  RobotOutlined,
  FileMarkdownOutlined,
} from "@ant-design/icons";
import { useSession } from "@/providers/SessionProvider";
import { FileContentRenderer } from "@/components/data-display/FileContentRenderer";

const { Text, Title } = Typography;

// 文件类型
interface ExportFile {
  name: string;
  path: string;
  size: number;
  modified: number;
  type: string;
}

// 预览内容
interface PreviewContent {
  content: string;
  type: "text" | "code" | "table" | "image";
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
    csv: <FileExcelOutlined style={{ color: "#52c41a" }} />,
    xlsx: <FileExcelOutlined style={{ color: "#52c41a" }} />,
    xls: <FileExcelOutlined style={{ color: "#52c41a" }} />,
    png: <FileImageOutlined style={{ color: "#1890ff" }} />,
    jpg: <FileImageOutlined style={{ color: "#1890ff" }} />,
    jpeg: <FileImageOutlined style={{ color: "#1890ff" }} />,
    gif: <FileImageOutlined style={{ color: "#1890ff" }} />,
    svg: <FileImageOutlined style={{ color: "#1890ff" }} />,
    json: <FileTextOutlined style={{ color: "#faad14" }} />,
    sql: <DatabaseOutlined style={{ color: "#722ed1" }} />,
    py: <CodeOutlined style={{ color: "#13c2c2" }} />,
    txt: <FileMarkdownOutlined style={{ color: "#1890ff" }} />,
    md: <FileMarkdownOutlined style={{ color: "#1890ff" }} />,
    pkl: <RobotOutlined style={{ color: "#eb2f96" }} />,
    joblib: <RobotOutlined style={{ color: "#eb2f96" }} />,
  };
  return iconMap[ext] || <FileOutlined />;
}

// 获取文件类型标签
function getFileTypeLabel(filename: string): { label: string; color: string } {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const typeMap: Record<string, { label: string; color: string }> = {
    csv: { label: "数据表", color: "green" },
    xlsx: { label: "Excel", color: "green" },
    png: { label: "图片", color: "blue" },
    jpg: { label: "图片", color: "blue" },
    jpeg: { label: "图片", color: "blue" },
    json: { label: "JSON", color: "orange" },
    sql: { label: "SQL", color: "purple" },
    py: { label: "Python", color: "cyan" },
    txt: { label: "文档", color: "blue" },
    md: { label: "Markdown", color: "blue" },
    pkl: { label: "模型", color: "magenta" },
    joblib: { label: "模型", color: "magenta" },
  };
  return typeMap[ext] || { label: ext.toUpperCase(), color: "default" };
}

export function ExportsPanel() {
  const { sessionId } = useSession();
  const [files, setFiles] = useState<ExportFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<ExportFile | null>(null);
  const [preview, setPreview] = useState<PreviewContent | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // 获取导出文件列表
  const fetchExports = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const url = sessionId
        ? `/api/sessions/exports?session_id=${sessionId}`
        : "/api/sessions/exports";
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error("获取导出文件失败");
      }
      const data = await res.json();
      setFiles(data.files || []);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchExports();
    const interval = setInterval(fetchExports, 10000);
    return () => clearInterval(interval);
  }, [fetchExports]);

  // 预览文件
  const handlePreview = async (file: ExportFile) => {
    setSelectedFile(file);
    setPreviewLoading(true);
    setPreview(null);

    try {
      const url = sessionId
        ? `/api/sessions/exports/${file.name}/preview?session_id=${sessionId}`
        : `/api/sessions/exports/${file.name}/preview`;
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error("预览失败");
      }
      const data = await res.json();
      setPreview(data);
    } catch (err) {
      setPreview({ content: `预览失败: ${(err as Error).message}`, type: "text" });
    } finally {
      setPreviewLoading(false);
    }
  };

  // 下载文件
  const handleDownload = (file: ExportFile) => {
    const url = sessionId
      ? `/api/sessions/exports/${file.name}/download?session_id=${sessionId}`
      : `/api/sessions/exports/${file.name}/download`;
    window.open(url, "_blank");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#fff" }}>
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
          <Title level={5} style={{ margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
            📦 导出文件
          </Title>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {loading ? "加载中..." : `${files.length} 个文件`}
          </Text>
        </div>
        <Button
          type="text"
          icon={<ReloadOutlined spin={loading} />}
          onClick={fetchExports}
          disabled={loading}
        />
      </div>

      {/* 文件列表 */}
      <div style={{ flex: 1, overflow: "auto" }}>
        {error ? (
          <div style={{ padding: 16 }}>
            <Alert
              message={error}
              type="error"
              action={
                <Button size="small" type="link" onClick={fetchExports}>
                  重试
                </Button>
              }
            />
          </div>
        ) : files.length === 0 && !loading ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span>
                暂无导出文件
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  执行数据分析任务后会自动生成
                </Text>
              </span>
            }
            style={{ marginTop: 48 }}
          />
        ) : (
          <List
            loading={loading}
            dataSource={files}
            renderItem={(file) => (
              <List.Item
                style={{
                  padding: "12px 16px",
                  cursor: "pointer",
                  background: selectedFile?.name === file.name ? "#e6f4ff" : "transparent",
                }}
                onClick={() => handlePreview(file)}
                actions={[
                  <Button
                    key="download"
                    type="text"
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(file);
                    }}
                  />,
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <span style={{ fontSize: 20 }}>{getFileIcon(file.name)}</span>
                  }
                  title={
                    <Tooltip title={file.name} placement="topLeft">
                      <Text ellipsis style={{ maxWidth: 280 }}>
                        {file.name}
                      </Text>
                    </Tooltip>
                  }
                  description={
                    <Space size={4}>
                      <Tag color={getFileTypeLabel(file.name).color} style={{ marginRight: 0 }}>
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
            <Tooltip title={selectedFile.name} placement="topLeft">
              <Text ellipsis style={{ maxWidth: 280 }}>
                预览: {selectedFile.name}
              </Text>
            </Tooltip>
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
          style={{ borderRadius: 0, borderLeft: 0, borderRight: 0, borderBottom: 0 }}
          styles={{ body: { padding: 0 } }}
        >
          <div style={{ padding: 12 }}>
            {previewLoading ? (
              <div style={{ textAlign: "center", padding: "20px 0" }}>
                <Spin size="small" />
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  加载中...
                </Text>
              </div>
            ) : preview ? (
              <FileContentRenderer
                filename={selectedFile.name}
                content={preview.content}
                compact
                maxHeight={250}
              />
            ) : null}
          </div>
          <div style={{ padding: 12 }}>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(selectedFile)}
              block
            >
              下载文件
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}

export default ExportsPanel;
