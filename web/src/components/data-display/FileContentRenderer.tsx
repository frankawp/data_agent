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
import { Typography, Image, Table, Tag, Empty } from "antd";
import type { ColumnsType } from "antd/es/table";
import { CodeViewer } from "./CodeViewer";

const { Text, Title, Paragraph } = Typography;

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
 * Markdown 渲染
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
      <MarkdownContent text={content} />
    </div>
  );
}

/**
 * Markdown 内容解析组件
 */
function MarkdownContent({ text }: { text: string }) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;
  let listItems: { type: "ul" | "ol"; items: string[] } | null = null;

  const flushList = () => {
    if (listItems) {
      const ListTag = listItems.type === "ol" ? "ol" : "ul";
      elements.push(
        <ListTag key={`list-${elements.length}`} style={{ margin: "8px 0", paddingLeft: 24 }}>
          {listItems.items.map((item, idx) => (
            <li key={idx} style={{ margin: "4px 0" }}>
              <InlineMarkdown text={item} />
            </li>
          ))}
        </ListTag>
      );
      listItems = null;
    }
  };

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // 空行
    if (!trimmed) {
      flushList();
      i++;
      continue;
    }

    // 标题 (# ## ### 等)
    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      flushList();
      const level = headingMatch[1].length as 1 | 2 | 3 | 4 | 5;
      elements.push(
        <Title key={`h-${i}`} level={level} style={{ marginTop: 16, marginBottom: 8 }}>
          <InlineMarkdown text={headingMatch[2]} />
        </Title>
      );
      i++;
      continue;
    }

    // 分隔线 (--- 或 ===)
    if (/^[-=]{3,}$/.test(trimmed)) {
      flushList();
      elements.push(<hr key={`hr-${i}`} style={{ margin: "16px 0", border: "none", borderTop: "1px solid #e8e8e8" }} />);
      i++;
      continue;
    }

    // 有序列表
    const olMatch = trimmed.match(/^(\d+)[.)]\s+(.+)$/);
    if (olMatch) {
      if (!listItems || listItems.type !== "ol") {
        flushList();
        listItems = { type: "ol", items: [] };
      }
      listItems.items.push(olMatch[2]);
      i++;
      continue;
    }

    // 无序列表
    const ulMatch = trimmed.match(/^[-*+]\s+(.+)$/);
    if (ulMatch) {
      if (!listItems || listItems.type !== "ul") {
        flushList();
        listItems = { type: "ul", items: [] };
      }
      listItems.items.push(ulMatch[1]);
      i++;
      continue;
    }

    // 代码块 (```)
    if (trimmed.startsWith("```")) {
      flushList();
      const lang = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // 跳过结束的 ```
      elements.push(
        <pre
          key={`code-${elements.length}`}
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
          {lang && (
            <Tag color="blue" style={{ marginBottom: 8 }}>
              {lang}
            </Tag>
          )}
          <code>{codeLines.join("\n")}</code>
        </pre>
      );
      continue;
    }

    // 引用 (>)
    if (trimmed.startsWith(">")) {
      flushList();
      const quoteLines: string[] = [trimmed.slice(1).trim()];
      i++;
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quoteLines.push(lines[i].trim().slice(1).trim());
        i++;
      }
      elements.push(
        <blockquote
          key={`quote-${elements.length}`}
          style={{
            borderLeft: "4px solid #d9d9d9",
            paddingLeft: 16,
            margin: "8px 0",
            color: "#666",
          }}
        >
          {quoteLines.map((ql, idx) => (
            <Paragraph key={idx} style={{ margin: "4px 0" }}>
              <InlineMarkdown text={ql} />
            </Paragraph>
          ))}
        </blockquote>
      );
      continue;
    }

    // 普通段落
    flushList();
    elements.push(
      <Paragraph key={`p-${i}`} style={{ margin: "8px 0" }}>
        <InlineMarkdown text={trimmed} />
      </Paragraph>
    );
    i++;
  }

  flushList();
  return <>{elements}</>;
}

/**
 * 行内 Markdown 格式处理（加粗、斜体、代码、链接）
 */
function InlineMarkdown({ text }: { text: string }) {
  // 匹配模式: **bold**, *italic*, `code`, [text](url)
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // 加粗 **text**
    const boldMatch = remaining.match(/^\*\*([^*]+)\*\*/);
    if (boldMatch) {
      parts.push(
        <strong key={key++} style={{ fontWeight: 600 }}>
          {boldMatch[1]}
        </strong>
      );
      remaining = remaining.slice(boldMatch[0].length);
      continue;
    }

    // 斜体 *text*
    const italicMatch = remaining.match(/^\*([^*]+)\*/);
    if (italicMatch) {
      parts.push(<em key={key++}>{italicMatch[1]}</em>);
      remaining = remaining.slice(italicMatch[0].length);
      continue;
    }

    // 行内代码 `code`
    const codeMatch = remaining.match(/^`([^`]+)`/);
    if (codeMatch) {
      parts.push(
        <code
          key={key++}
          style={{
            background: "#f0f0f0",
            padding: "2px 6px",
            borderRadius: 3,
            fontSize: "0.9em",
            fontFamily: "monospace",
          }}
        >
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeMatch[0].length);
      continue;
    }

    // 链接 [text](url)
    const linkMatch = remaining.match(/^\[([^\]]+)\]\(([^)]+)\)/);
    if (linkMatch) {
      parts.push(
        <a key={key++} href={linkMatch[2]} target="_blank" rel="noopener noreferrer" style={{ color: "#1890ff" }}>
          {linkMatch[1]}
        </a>
      );
      remaining = remaining.slice(linkMatch[0].length);
      continue;
    }

    // 普通文本（取到下一个特殊字符或结束）
    const nextSpecial = remaining.search(/[\*`\[]/);
    if (nextSpecial === -1) {
      parts.push(<span key={key++}>{remaining}</span>);
      break;
    } else if (nextSpecial === 0) {
      // 特殊字符但未匹配到模式，当作普通字符处理
      parts.push(<span key={key++}>{remaining[0]}</span>);
      remaining = remaining.slice(1);
    } else {
      parts.push(<span key={key++}>{remaining.slice(0, nextSpecial)}</span>);
      remaining = remaining.slice(nextSpecial);
    }
  }

  return <>{parts}</>;
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
