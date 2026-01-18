"use client";

/**
 * 文件内容渲染组件
 *
 * 根据文件类型自动选择合适的渲染方式：
 * - csv: 表格展示
 * - md/txt: Markdown 渲染
 * - sql: SQL 代码高亮
 * - py: Python 代码高亮
 * - png/jpg: 图片展示
 * - json: JSON 格式化
 */

import React from "react";
import { Typography, Image, Table, Empty } from "antd";
import type { ColumnsType } from "antd/es/table";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CodeViewer } from "./CodeViewer";

const { Text } = Typography;

// 文件类型
type FileType = "csv" | "md" | "txt" | "sql" | "py" | "png" | "jpg" | "jpeg" | "json" | "unknown";

interface FileContentRendererProps {
  /** 文件名（用于判断类型） */
  filename: string;
  /** 文件内容 */
  content: string;
  /** 是否紧凑模式 */
  compact?: boolean;
  /** 最大高度 */
  maxHeight?: number;
}

// 获取文件扩展名
function getFileExtension(filename: string): FileType {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const validTypes: FileType[] = ["csv", "md", "txt", "sql", "py", "png", "jpg", "jpeg", "json"];
  return validTypes.includes(ext as FileType) ? (ext as FileType) : "unknown";
}

/**
 * 文件内容渲染器
 */
export function FileContentRenderer({ filename, content, compact = false, maxHeight = 300 }: FileContentRendererProps) {
  const fileType = getFileExtension(filename);

  switch (fileType) {
    case "csv":
      return <CSVRenderer content={content} compact={compact} maxHeight={maxHeight} />;

    case "md":
    case "txt":
      return <MarkdownRenderer content={content} compact={compact} maxHeight={maxHeight} />;

    case "sql":
      return <CodeViewer code={content} language="sql" maxHeight={maxHeight} />;

    case "py":
      return <CodeViewer code={content} language="python" maxHeight={maxHeight} />;

    case "png":
    case "jpg":
    case "jpeg":
      return <Image src={content} alt={filename} style={{ maxWidth: "100%", maxHeight }} />;

    case "json":
      return <JSONRenderer content={content} compact={compact} maxHeight={maxHeight} />;

    default:
      return <PlainTextRenderer content={content} maxHeight={maxHeight} />;
  }
}

/**
 * CSV 表格渲染
 */
function CSVRenderer({ content, compact, maxHeight }: { content: string; compact?: boolean; maxHeight?: number }) {
  const lines = content.trim().split("\n");
  if (lines.length === 0) {
    return <Empty description="无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
  }

  // 解析 CSV
  const parseCSVLine = (line: string): string[] => {
    const result: string[] = [];
    let current = "";
    let inQuotes = false;
    for (const char of line) {
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === "," && !inQuotes) {
        result.push(current.trim());
        current = "";
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  };

  const headers = parseCSVLine(lines[0]);
  const rows = lines.slice(1).map(parseCSVLine);

  const columns: ColumnsType<Record<string, string>> = headers.map((col, index) => ({
    title: col,
    dataIndex: `col_${index}`,
    key: `col_${index}`,
    ellipsis: true,
    width: compact ? 100 : 150,
    render: (text: string) => (
      <Text ellipsis={{ tooltip: text }} style={{ fontSize: compact ? 12 : 14 }}>
        {text}
      </Text>
    ),
  }));

  const dataSource = rows.map((row, rowIndex) => {
    const record: Record<string, string> = { key: `row_${rowIndex}` };
    row.forEach((cell, colIndex) => {
      record[`col_${colIndex}`] = cell;
    });
    return record;
  });

  return (
    <div style={{ maxHeight, overflow: "auto" }}>
      <Table
        columns={columns}
        dataSource={dataSource.slice(0, compact ? 10 : 100)}
        size="small"
        scroll={{ x: "max-content" }}
        pagination={false}
        bordered
      />
      {dataSource.length > (compact ? 10 : 100) && (
        <Text type="secondary" style={{ fontSize: 12, display: "block", marginTop: 4 }}>
          显示前 {compact ? 10 : 100} 行，共 {dataSource.length} 行
        </Text>
      )}
    </div>
  );
}

/**
 * Markdown 渲染 - 使用 react-markdown
 */
function MarkdownRenderer({ content, compact, maxHeight }: { content: string; compact?: boolean; maxHeight?: number }) {
  return (
    <div
      className="markdown-content"
      style={{
        maxHeight,
        overflow: "auto",
        fontSize: compact ? 13 : 14,
        lineHeight: 1.8,
        padding: compact ? 8 : 12,
        background: "#fafafa",
        borderRadius: 4,
      }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 自定义代码块样式
          pre: ({ children }) => (
            <pre
              style={{
                background: "#1a1a2e",
                color: "#e0e0e0",
                padding: 12,
                borderRadius: 4,
                overflow: "auto",
                fontSize: 12,
                margin: "8px 0",
              }}
            >
              {children}
            </pre>
          ),
          // 自定义行内代码
          code: ({ children, className }) => {
            // 如果有 className，说明是代码块内的代码
            if (className) {
              return <code>{children}</code>;
            }
            // 否则是行内代码
            return (
              <code
                style={{
                  background: "#f0f0f0",
                  padding: "2px 6px",
                  borderRadius: 3,
                  fontSize: "0.9em",
                  fontFamily: "monospace",
                }}
              >
                {children}
              </code>
            );
          },
          // 自定义引用块
          blockquote: ({ children }) => (
            <blockquote
              style={{
                borderLeft: "4px solid #d9d9d9",
                paddingLeft: 16,
                margin: "8px 0",
                color: "#666",
              }}
            >
              {children}
            </blockquote>
          ),
          // 自定义链接
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#1890ff" }}>
              {children}
            </a>
          ),
          // 自定义标题
          h1: ({ children }) => <h1 style={{ marginTop: 16, marginBottom: 8, fontSize: 24, fontWeight: 600 }}>{children}</h1>,
          h2: ({ children }) => <h2 style={{ marginTop: 16, marginBottom: 8, fontSize: 20, fontWeight: 600 }}>{children}</h2>,
          h3: ({ children }) => <h3 style={{ marginTop: 16, marginBottom: 8, fontSize: 16, fontWeight: 600 }}>{children}</h3>,
          h4: ({ children }) => <h4 style={{ marginTop: 12, marginBottom: 6, fontSize: 14, fontWeight: 600 }}>{children}</h4>,
          // 自定义表格
          table: ({ children }) => (
            <table
              style={{
                borderCollapse: "collapse",
                width: "100%",
                margin: "8px 0",
                fontSize: 13,
              }}
            >
              {children}
            </table>
          ),
          th: ({ children }) => (
            <th
              style={{
                border: "1px solid #e8e8e8",
                padding: "8px 12px",
                background: "#fafafa",
                fontWeight: 600,
                textAlign: "left",
              }}
            >
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td
              style={{
                border: "1px solid #e8e8e8",
                padding: "8px 12px",
              }}
            >
              {children}
            </td>
          ),
          // 自定义列表
          ul: ({ children }) => <ul style={{ margin: "8px 0", paddingLeft: 24 }}>{children}</ul>,
          ol: ({ children }) => <ol style={{ margin: "8px 0", paddingLeft: 24 }}>{children}</ol>,
          li: ({ children }) => <li style={{ margin: "4px 0" }}>{children}</li>,
          // 自定义段落
          p: ({ children }) => <p style={{ margin: "8px 0" }}>{children}</p>,
          // 自定义分隔线
          hr: () => <hr style={{ margin: "16px 0", border: "none", borderTop: "1px solid #e8e8e8" }} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

/**
 * JSON 渲染
 */
function JSONRenderer({ content, compact, maxHeight }: { content: string; compact?: boolean; maxHeight?: number }) {
  let formatted: string;
  try {
    const parsed = JSON.parse(content);
    formatted = JSON.stringify(parsed, null, 2);
  } catch {
    formatted = content;
  }

  return (
    <pre
      style={{
        background: "#1a1a2e",
        color: "#e0e0e0",
        padding: compact ? 8 : 12,
        borderRadius: 4,
        overflow: "auto",
        fontSize: compact ? 11 : 12,
        maxHeight,
        margin: 0,
      }}
    >
      {formatted}
    </pre>
  );
}

/**
 * 纯文本渲染
 */
function PlainTextRenderer({ content, maxHeight }: { content: string; maxHeight?: number }) {
  return (
    <pre
      style={{
        background: "#f5f5f5",
        padding: 12,
        borderRadius: 4,
        overflow: "auto",
        fontSize: 12,
        maxHeight,
        margin: 0,
        whiteSpace: "pre-wrap",
        wordBreak: "break-all",
      }}
    >
      {content}
    </pre>
  );
}

export default FileContentRenderer;
