"use client";

/**
 * 可放大查看的内容包装组件
 *
 * 在内容框右上角显示放大按钮，点击后弹出 Modal 显示完整内容。
 */

import { useState, ReactNode } from "react";
import { Modal, Button, Tooltip } from "antd";
import { ExpandAltOutlined, CompressOutlined } from "@ant-design/icons";

interface ExpandableContentProps {
  children: ReactNode;
  /** Modal 中显示的内容，如果不提供则使用 children */
  expandedContent?: ReactNode;
  /** Modal 标题 */
  title?: string;
  /** 是否显示放大按钮 */
  expandable?: boolean;
  /** 按钮位置偏移 */
  buttonOffset?: { top?: number; right?: number };
}

export function ExpandableContent({
  children,
  expandedContent,
  title = "详细内容",
  expandable = true,
  buttonOffset = { top: 8, right: 8 },
}: ExpandableContentProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (!expandable) {
    return <>{children}</>;
  }

  return (
    <div style={{ position: "relative" }}>
      {children}
      <Tooltip title="放大查看">
        <Button
          type="text"
          size="small"
          icon={<ExpandAltOutlined />}
          onClick={() => setIsModalOpen(true)}
          style={{
            position: "absolute",
            top: buttonOffset.top,
            right: buttonOffset.right,
            opacity: 0.6,
            zIndex: 10,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
        />
      </Tooltip>
      <Modal
        title={title}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        width="90vw"
        style={{ top: 20 }}
        styles={{
          body: {
            maxHeight: "80vh",
            overflow: "auto",
            padding: 16,
          },
        }}
      >
        {expandedContent || children}
      </Modal>
    </div>
  );
}

/**
 * 代码内容的放大查看组件
 *
 * 专门用于代码块，Modal 中使用深色主题。
 */
interface ExpandableCodeProps {
  code: string;
  language?: string;
  title?: string;
  children: ReactNode;
  buttonOffset?: { top?: number; right?: number };
}

export function ExpandableCode({
  code,
  language = "text",
  title,
  children,
  buttonOffset = { top: 8, right: 40 },
}: ExpandableCodeProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const modalTitle = title || `${language.toUpperCase()} 代码`;

  return (
    <div style={{ position: "relative" }}>
      {children}
      <Tooltip title="放大查看">
        <Button
          type="text"
          size="small"
          icon={<ExpandAltOutlined />}
          onClick={() => setIsModalOpen(true)}
          style={{
            position: "absolute",
            top: buttonOffset.top,
            right: buttonOffset.right,
            opacity: 0.6,
            zIndex: 10,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
        />
      </Tooltip>
      <Modal
        title={modalTitle}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        width="90vw"
        style={{ top: 20 }}
        styles={{
          body: {
            maxHeight: "80vh",
            overflow: "auto",
            padding: 0,
          },
        }}
      >
        <pre
          style={{
            margin: 0,
            padding: 20,
            fontSize: 14,
            lineHeight: 1.6,
            background: "#1a1a2e",
            color: "#e0e0e0",
            borderRadius: 4,
            overflow: "auto",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          <code>{code}</code>
        </pre>
      </Modal>
    </div>
  );
}

/**
 * 表格内容的放大查看组件
 */
interface ExpandableTableProps {
  children: ReactNode;
  expandedContent: ReactNode;
  title?: string;
  buttonOffset?: { top?: number; right?: number };
}

export function ExpandableTable({
  children,
  expandedContent,
  title = "数据表",
  buttonOffset = { top: -36, right: 0 },
}: ExpandableTableProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div style={{ position: "relative" }}>
      <Tooltip title="放大查看">
        <Button
          type="text"
          size="small"
          icon={<ExpandAltOutlined />}
          onClick={() => setIsModalOpen(true)}
          style={{
            position: "absolute",
            top: buttonOffset.top,
            right: buttonOffset.right,
            opacity: 0.6,
            zIndex: 10,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
        />
      </Tooltip>
      {children}
      <Modal
        title={title}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        width="95vw"
        style={{ top: 20 }}
        styles={{
          body: {
            maxHeight: "85vh",
            overflow: "auto",
            padding: 16,
          },
        }}
      >
        {expandedContent}
      </Modal>
    </div>
  );
}

export default ExpandableContent;
