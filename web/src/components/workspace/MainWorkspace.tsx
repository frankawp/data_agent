"use client";

/**
 * 主工作区组件
 *
 * 使用 Ant Design 组件重构，显示 AI 执行步骤和结果。
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Card,
  Tag,
  Typography,
  Empty,
  Spin,
  Button,
  Badge,
  Timeline,
  Alert,
  List,
  theme,
  Modal,
  Tooltip,
} from "antd";
import {
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
  ArrowDownOutlined,
  CodeOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  RobotOutlined,
  HistoryOutlined,
  OrderedListOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  ExpandAltOutlined,
} from "@ant-design/icons";
import { useWorkspace, StreamingStep, SubagentStep } from "@/hooks/useWorkspaceContext";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CodeViewer } from "@/components/data-display/CodeViewer";
import { DataTable } from "@/components/data-display/DataTable";
import { FileContentRenderer } from "@/components/data-display/FileContentRenderer";

const { Title, Text, Paragraph } = Typography;

export function MainWorkspace() {
  const {
    viewMode,
    historicalStep,
    exitHistoricalView,
    currentToolResult,
    isStreaming,
    streamingSteps,
  } = useWorkspace();

  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [hasNewContent, setHasNewContent] = useState(false);
  const prevStepsCountRef = useRef(streamingSteps.length);

  const checkIfAtBottom = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return true;
    return container.scrollHeight - container.scrollTop - container.clientHeight < 100;
  }, []);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollContainerRef.current?.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
      setHasNewContent(false);
      setIsAtBottom(true);
    });
  }, []);

  useEffect(() => {
    if (streamingSteps.length > prevStepsCountRef.current) {
      if (isAtBottom) {
        setTimeout(scrollToBottom, 50);
      } else {
        setHasNewContent(true);
      }
    }
    prevStepsCountRef.current = streamingSteps.length;
  }, [streamingSteps.length, isAtBottom, scrollToBottom]);

  useEffect(() => {
    if (isStreaming && streamingSteps.length === 0) {
      scrollToBottom();
    }
  }, [isStreaming, streamingSteps.length, scrollToBottom]);

  const { token } = theme.useToken();

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: token.colorBgContainer,
        transition: "background 0.25s ease",
        position: "relative",
      }}
    >
      {/* 标题栏 */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: `${token.paddingSM}px ${token.padding}px`,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          background: token.colorFillTertiary,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: token.marginSM }}>
          <ThunderboltOutlined style={{ fontSize: 16, color: token.colorPrimary }} />
          <Text strong>实时输出</Text>
          {isStreaming && <Badge status="processing" text="执行中" />}
        </div>
      </div>

      {/* 历史模式提示 */}
      {viewMode === "historical" && historicalStep && (
        <Alert
          message={`正在查看历史步骤 #${historicalStep.index}: ${historicalStep.toolName}`}
          type="warning"
          showIcon
          icon={<HistoryOutlined />}
          action={
            <Button size="small" type="primary" onClick={exitHistoricalView}>
              退出历史查看
            </Button>
          }
          style={{ borderRadius: 0 }}
        />
      )}

      {/* 内容区域 */}
      <div
        ref={scrollContainerRef}
        onScroll={() => {
          const atBottom = checkIfAtBottom();
          setIsAtBottom(atBottom);
          if (atBottom) setHasNewContent(false);
        }}
        style={{ flex: 1, overflow: "auto", padding: token.padding }}
      >
        {viewMode === "live" ? (
          isStreaming || streamingSteps.length > 0 ? (
            <StreamingContent steps={streamingSteps} isStreaming={isStreaming} />
          ) : (
            <LiveContent toolResult={currentToolResult} />
          )
        ) : (
          <HistoricalContent step={historicalStep} />
        )}
      </div>

      {/* 新内容提示 */}
      {hasNewContent && !isAtBottom && (
        <Button
          type="primary"
          icon={<ArrowDownOutlined />}
          onClick={scrollToBottom}
          className="animate-bounce"
          style={{
            position: "absolute",
            bottom: 24,
            left: "50%",
            transform: "translateX(-50%)",
            borderRadius: 20,
            boxShadow: token.boxShadowSecondary,
            paddingLeft: 16,
            paddingRight: 16,
          }}
        >
          有新内容
        </Button>
      )}
    </div>
  );
}

// 工具名称和图标映射
const toolInfo: Record<string, { name: string; icon: React.ReactNode; color: string }> = {
  execute_sql: { name: "SQL 查询", icon: <DatabaseOutlined />, color: "blue" },
  execute_python_safe: { name: "Python 执行", icon: <CodeOutlined />, color: "green" },
  list_tables: { name: "列出表", icon: <DatabaseOutlined />, color: "cyan" },
  describe_table: { name: "表结构", icon: <FileTextOutlined />, color: "purple" },
  train_model: { name: "模型训练", icon: <ExperimentOutlined />, color: "magenta" },
  predict: { name: "模型预测", icon: <ExperimentOutlined />, color: "orange" },
  task: { name: "子代理任务", icon: <RobotOutlined />, color: "geekblue" },
  write_todos: { name: "任务规划", icon: <OrderedListOutlined />, color: "gold" },
  ls: { name: "文件列表", icon: <FileTextOutlined />, color: "default" },
  read_file: { name: "读取文件", icon: <FileTextOutlined />, color: "default" },
  write_file: { name: "写入文件", icon: <FileTextOutlined />, color: "green" },
};

function getToolInfo(toolName: string) {
  return toolInfo[toolName] || { name: toolName, icon: <CodeOutlined />, color: "default" };
}

/**
 * 可展开的代码/结果显示组件
 */
function ExpandablePreview({
  content,
  label,
  maxHeight = 150,
  darkTheme = false,
  modalTitle,
}: {
  content: string;
  label: string;
  maxHeight?: number;
  darkTheme?: boolean;
  modalTitle?: string;
}) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const preStyle: React.CSSProperties = darkTheme
    ? {
        margin: 0,
        padding: 8,
        background: "#1a1a2e",
        color: "#a6e22e",
        borderRadius: 4,
        fontSize: 11,
        fontFamily: "monospace",
        overflow: "auto",
        maxHeight,
        whiteSpace: "pre-wrap",
        wordBreak: "break-all",
      }
    : {
        margin: 0,
        padding: 8,
        background: "#f5f5f5",
        borderRadius: 4,
        fontSize: 11,
        fontFamily: "monospace",
        overflow: "auto",
        maxHeight,
        whiteSpace: "pre-wrap",
        wordBreak: "break-all",
      };

  const modalPreStyle: React.CSSProperties = {
    margin: 0,
    padding: 16,
    background: "#1e1e1e",
    color: "#d4d4d4",
    borderRadius: 4,
    fontSize: 13,
    lineHeight: 1.6,
    fontFamily: "monospace",
    overflow: "auto",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  };

  return (
    <div style={{ position: "relative" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
        <Text type="secondary" style={{ fontSize: 11 }}>
          {label}
        </Text>
        <Tooltip title="放大查看">
          <Button
            type="text"
            size="small"
            icon={<ExpandAltOutlined />}
            onClick={() => setIsModalOpen(true)}
            style={{ opacity: 0.6, height: 20, width: 20, minWidth: 20 }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
          />
        </Tooltip>
      </div>
      <pre style={preStyle}>{content || "无内容"}</pre>
      <Modal
        title={modalTitle || label}
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
        <pre style={modalPreStyle}>{content || "无内容"}</pre>
      </Modal>
    </div>
  );
}

/**
 * 可展开的 Markdown 内容组件
 */
function ExpandableMarkdown({
  content,
  maxHeight = 400,
  modalTitle = "详细内容",
}: {
  content: string;
  maxHeight?: number;
  modalTitle?: string;
}) {
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
            top: 8,
            right: 8,
            opacity: 0.6,
            zIndex: 10,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
        />
      </Tooltip>
      <div style={{ background: "#fafafa", padding: 12, borderRadius: 4, maxHeight, overflow: "auto" }}>
        <SimpleMarkdown text={content} />
      </div>
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
            padding: 16,
          },
        }}
      >
        <SimpleMarkdown text={content} />
      </Modal>
    </div>
  );
}

/**
 * 可展开的文件内容组件
 */
function ExpandableFileContent({
  filePath,
  filename,
  content,
}: {
  filePath: string;
  filename: string;
  content: string;
}) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div style={{ position: "relative" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        {filePath && (
          <Tag color="blue">
            📄 {filePath}
          </Tag>
        )}
        <Tooltip title="放大查看">
          <Button
            type="text"
            size="small"
            icon={<ExpandAltOutlined />}
            onClick={() => setIsModalOpen(true)}
            style={{ opacity: 0.6 }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
          />
        </Tooltip>
      </div>
      <FileContentRenderer
        filename={filename}
        content={content}
        compact
        maxHeight={150}
      />
      <Modal
        title={`文件内容 - ${filename}`}
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
        <FileContentRenderer
          filename={filename}
          content={content}
          maxHeight={undefined}
        />
      </Modal>
    </div>
  );
}

// 流式执行内容
function StreamingContent({ steps, isStreaming }: { steps: StreamingStep[]; isStreaming: boolean }) {
  const { token } = theme.useToken();

  if (steps.length === 0 && isStreaming) {
    return (
      <div
        className="animate-fade-in"
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          minHeight: 300,
        }}
      >
        <Spin size="large" />
        <Text type="secondary" style={{ fontSize: 16, marginTop: token.marginLG }}>
          AI 正在分析任务...
        </Text>
      </div>
    );
  }

  const completedCount = steps.filter((s) => s.status === "completed").length;

  return (
    <div className="animate-fade-in">
      {/* 进度概览 */}
      <Card
        size="small"
        style={{
          marginBottom: token.margin,
          borderRadius: token.borderRadiusLG,
          boxShadow: token.boxShadow,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Title level={5} style={{ margin: 0 }}>
            执行步骤 ({completedCount}/{steps.length})
          </Title>
          {isStreaming && (
            <Tag color="processing" icon={<LoadingOutlined />}>
              执行中
            </Tag>
          )}
        </div>
      </Card>

      {/* 步骤时间线 */}
      <Timeline
        items={steps.map((step) => {
          const info = getToolInfo(step.toolName);
          const statusIcon =
            step.status === "completed" ? (
              <CheckCircleOutlined style={{ color: token.colorSuccess }} />
            ) : step.status === "error" ? (
              <CloseCircleOutlined style={{ color: token.colorError }} />
            ) : (
              <LoadingOutlined style={{ color: token.colorPrimary }} />
            );

          return {
            dot: statusIcon,
            children: <StepCard step={step} info={info} />,
          };
        })}
      />
    </div>
  );
}

// 步骤卡片
function StepCard({
  step,
  info,
}: {
  step: StreamingStep;
  info: { name: string; icon: React.ReactNode; color: string };
}) {
  const { token } = theme.useToken();
  const borderColor =
    step.status === "completed"
      ? token.colorSuccess
      : step.status === "error"
        ? token.colorError
        : token.colorPrimary;

  return (
    <Card
      size="small"
      className="animate-fade-in-up"
      style={{
        borderLeft: `3px solid ${borderColor}`,
        marginBottom: token.marginSM,
        borderRadius: token.borderRadius,
      }}
      styles={{ body: { padding: `${token.paddingSM}px ${token.padding}px` } }}
    >
      {/* 步骤头部 */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: token.marginSM,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: token.marginSM }}>
          <Tag color={info.color} icon={info.icon}>
            {info.name}
          </Tag>
          <Text type="secondary">Step {step.step}</Text>
        </div>
        {step.status === "running" && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            <LoadingOutlined style={{ marginRight: 4 }} />
            执行中...
          </Text>
        )}
      </div>

      {/* 参数展示 */}
      {step.args && Object.keys(step.args).length > 0 && (
        <StepArgsDisplay toolName={step.toolName} args={step.args} />
      )}

      {/* 子代理步骤 */}
      {step.toolName === "task" && step.subagentSteps && step.subagentSteps.length > 0 && (
        <div
          style={{
            marginTop: token.marginSM,
            marginLeft: token.margin,
            borderLeft: `2px solid ${token.colorInfoBg}`,
            paddingLeft: token.paddingSM,
          }}
        >
          <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: token.marginSM }}>
            <RobotOutlined style={{ marginRight: 4 }} />
            {step.subagentName || "子代理"} 执行步骤:
          </Text>
          {step.subagentSteps.map((substep) => (
            <SubagentStepCard key={`${substep.subagentName}-${substep.step}`} substep={substep} />
          ))}
        </div>
      )}

      {/* 执行结果 */}
      {step.result && (
        <div
          style={{
            marginTop: token.marginSM,
            paddingTop: token.paddingSM,
            borderTop: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: token.marginSM }}>
            执行结果:
          </Text>
          <StepResultDisplay toolName={step.toolName} result={step.result} />
        </div>
      )}
    </Card>
  );
}

// Markdown 渲染组件 - 使用 react-markdown
function SimpleMarkdown({ text }: { text: string }) {
  return (
    <div style={{ fontSize: 13, lineHeight: 1.8 }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 自定义段落
          p: ({ children }) => <p style={{ margin: "6px 0" }}>{children}</p>,
          // 自定义列表
          ul: ({ children }) => <ul style={{ margin: "8px 0", paddingLeft: 24 }}>{children}</ul>,
          ol: ({ children }) => <ol style={{ margin: "8px 0", paddingLeft: 24 }}>{children}</ol>,
          li: ({ children }) => <li style={{ margin: "4px 0" }}>{children}</li>,
          // 加粗样式
          strong: ({ children }) => (
            <strong style={{ color: "#389e0d", fontWeight: 600 }}>{children}</strong>
          ),
          // 行内代码
          code: ({ children, className }) => {
            if (className) return <code>{children}</code>;
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
          // 代码块
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
          // 链接
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#1890ff" }}>
              {children}
            </a>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}

// TODO 项目接口
interface TodoItem {
  content: string;
  status: "pending" | "in_progress" | "completed";
}

// 解析 TODO 列表
function parseTodos(args: Record<string, unknown>): TodoItem[] {
  const todos = args.todos;
  if (!todos || !Array.isArray(todos)) return [];
  return todos.map((item) => ({
    content: String((item as Record<string, unknown>).content || ""),
    status: ((item as Record<string, unknown>).status as TodoItem["status"]) || "pending",
  }));
}

// TODO 列表展示组件
function TodoListDisplay({ todos }: { todos: TodoItem[] }) {
  if (todos.length === 0) return null;

  const statusConfig = {
    pending: { icon: <ClockCircleOutlined />, color: "default", text: "待处理" },
    in_progress: { icon: <LoadingOutlined />, color: "processing", text: "进行中" },
    completed: { icon: <CheckCircleOutlined />, color: "success", text: "已完成" },
  };

  return (
    <List
      size="small"
      dataSource={todos}
      renderItem={(item, index) => {
        const config = statusConfig[item.status];
        return (
          <List.Item style={{ padding: "8px 0", borderBottom: "1px solid #f0f0f0" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 8, width: "100%" }}>
              <Text type="secondary" style={{ minWidth: 20 }}>{index + 1}.</Text>
              <div style={{ flex: 1 }}>
                <Text style={{
                  textDecoration: item.status === "completed" ? "line-through" : "none",
                  color: item.status === "completed" ? "#8c8c8c" : "inherit"
                }}>
                  {item.content}
                </Text>
              </div>
              <Tag icon={config.icon} color={config.color} style={{ marginLeft: 8 }}>
                {config.text}
              </Tag>
            </div>
          </List.Item>
        );
      }}
    />
  );
}

// 参数展示
function StepArgsDisplay({ toolName, args }: { toolName: string; args: Record<string, unknown> }) {
  switch (toolName) {
    case "execute_sql":
      return <CodeViewer code={(args.query as string) || ""} language="sql" />;
    case "execute_python_safe":
      return <CodeViewer code={(args.code as string) || ""} language="python" />;
    case "describe_table":
      return (
        <Text>
          表名: <Tag>{args.table_name as string}</Tag>
        </Text>
      );
    case "write_todos": {
      const todos = parseTodos(args);
      const completed = todos.filter((t) => t.status === "completed").length;
      const inProgress = todos.filter((t) => t.status === "in_progress").length;
      return (
        <Card
          size="small"
          style={{ background: "#fffbe6", border: "1px solid #ffe58f" }}
          title={
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span>
                <OrderedListOutlined style={{ marginRight: 8, color: "#faad14" }} />
                任务清单
              </span>
              <Text type="secondary" style={{ fontSize: 12, fontWeight: "normal" }}>
                {completed}/{todos.length} 已完成
                {inProgress > 0 && ` · ${inProgress} 进行中`}
              </Text>
            </div>
          }
        >
          <TodoListDisplay todos={todos} />
        </Card>
      );
    }
    case "task": {
      const description = args.description ? String(args.description) : "";
      return (
        <Card size="small" style={{ background: "#f6ffed", border: "1px solid #b7eb8f" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: description ? 8 : 0 }}>
            <RobotOutlined style={{ color: "#52c41a" }} />
            <Text strong>{(args.subagent_type as string) || "子代理"}</Text>
          </div>
          {description && <SimpleMarkdown text={description} />}
        </Card>
      );
    }
    default:
      return (
        <pre style={{ fontSize: 12, background: "#fafafa", padding: 8, borderRadius: 4, overflow: "auto", margin: 0 }}>
          {JSON.stringify(args, null, 2)}
        </pre>
      );
  }
}

// 子代理步骤结果格式化
function formatSubagentResult(toolName: string, result: string, args?: Record<string, unknown>): React.ReactNode {
  if (!result || result === "[Command returned]") {
    return <Text type="secondary">已完成</Text>;
  }

  switch (toolName) {
    case "write_todos": {
      // 任务规划 - 显示简洁提示
      return <Text type="secondary">任务规划已更新</Text>;
    }

    case "list_tables": {
      // 列出表 - 解析表名列表并美化展示
      const tableMatch = result.match(/数据库中的表:\s*[-–]\s*(.+)/);
      if (tableMatch) {
        const tables = tableMatch[1].split(/\s*[-–]\s*/).filter(Boolean);
        return (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
            {tables.slice(0, 8).map((table, i) => (
              <Tag key={i} color="blue" style={{ margin: 0 }}>
                {table.trim()}
              </Tag>
            ))}
            {tables.length > 8 && (
              <Tag color="default">+{tables.length - 8} 更多</Tag>
            )}
          </div>
        );
      }
      return <Text type="secondary">{result.slice(0, 100)}...</Text>;
    }

    case "describe_table": {
      // 表结构 - 解析字段信息
      const tableNameMatch = result.match(/表\s+(\w+)\s+的结构/);
      const tableName = tableNameMatch ? tableNameMatch[1] : "";

      // 解析字段（格式: Field Type Null Key Default Extra 0 field_name type ...）
      const fieldsMatch = result.match(/\d+\s+(\w+)\s+(\w+)/g);
      if (fieldsMatch && fieldsMatch.length > 0) {
        const fields = fieldsMatch.slice(0, 5).map((f) => {
          const parts = f.trim().split(/\s+/);
          return { name: parts[1], type: parts[2] };
        });
        return (
          <div>
            {tableName && (
              <Text strong style={{ fontSize: 12 }}>
                表 <Tag color="purple" style={{ margin: "0 4px" }}>{tableName}</Tag>
              </Text>
            )}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
              {fields.map((field, i) => (
                <Tag key={i} style={{ margin: 0 }}>
                  {field.name} <Text type="secondary" style={{ fontSize: 11 }}>({field.type})</Text>
                </Tag>
              ))}
              {fieldsMatch.length > 5 && (
                <Tag color="default">+{fieldsMatch.length - 5} 字段</Tag>
              )}
            </div>
          </div>
        );
      }
      return <Text type="secondary">{result.slice(0, 80)}...</Text>;
    }

    case "execute_sql": {
      // SQL 查询 - 显示 SQL 语句和表格结果
      const query = args?.query ? String(args.query) : "";
      return (
        <div>
          {query && (
            <div style={{ marginBottom: 8 }}>
              <Text type="secondary" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>
                SQL 语句:
              </Text>
              <pre
                style={{
                  margin: 0,
                  padding: 8,
                  background: "#f6f8fa",
                  borderRadius: 4,
                  fontSize: 11,
                  fontFamily: "monospace",
                  overflow: "auto",
                  maxHeight: 80,
                  border: "1px solid #e8e8e8",
                }}
              >
                {query}
              </pre>
            </div>
          )}
          <Text type="secondary" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>
            查询结果:
          </Text>
          <DataTable data={parseTableData(result)} maxRows={5} compact />
        </div>
      );
    }

    case "execute_python_safe": {
      // Python 执行 - 显示代码和完整输出
      const code = args?.code ? String(args.code) : "";
      return (
        <div>
          {code && (
            <div style={{ marginBottom: 8 }}>
              <ExpandablePreview
                content={code}
                label="执行代码:"
                maxHeight={150}
                darkTheme
                modalTitle="Python 代码"
              />
            </div>
          )}
          <ExpandablePreview
            content={result || "执行完成，无输出"}
            label="执行结果:"
            maxHeight={200}
            modalTitle="执行结果"
          />
        </div>
      );
    }

    case "ls": {
      // 文件列表 - 显示路径和内容，支持放大查看
      const path = args?.path ? String(args.path) : "";
      return (
        <div>
          <ExpandablePreview
            content={result}
            label={path ? `📁 ${path}` : "文件列表:"}
            maxHeight={100}
            modalTitle={`文件列表 - ${path || "/"}`}
          />
        </div>
      );
    }

    case "read_file": {
      // 读取文件 - 根据文件类型渲染内容，支持放大查看
      const filePath = args?.path ? String(args.path) : (args?.file_path ? String(args.file_path) : "");
      const filename = filePath.split("/").pop() || "file.txt";
      return (
        <ExpandableFileContent
          filePath={filePath}
          filename={filename}
          content={result}
        />
      );
    }

    case "write_file": {
      // 写入文件 - 显示文件路径和写入的内容
      const filePath = args?.path ? String(args.path) : (args?.file_path ? String(args.file_path) : "");
      const content = args?.content ? String(args.content) : "";
      const filename = filePath.split("/").pop() || "file.txt";

      // 检查是否有实际内容写入
      const hasContent = content && content.trim().length > 0;

      return (
        <div>
          <Tag color="green" style={{ marginBottom: 6 }}>
            ✏️ 写入: {filePath || "未知路径"}
          </Tag>
          {hasContent ? (
            <FileContentRenderer
              filename={filename}
              content={content}
              compact
              maxHeight={200}
            />
          ) : (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {result || "文件写入成功"}
            </Text>
          )}
        </div>
      );
    }

    default: {
      // 默认 - 简化显示
      const preview = result.slice(0, 80).replace(/\n/g, " ");
      return <Text type="secondary">{preview}{result.length > 80 ? "..." : ""}</Text>;
    }
  }
}

// 子代理步骤卡片
function SubagentStepCard({ substep }: { substep: SubagentStep }) {
  const info = getToolInfo(substep.toolName);
  const statusIcon =
    substep.status === "completed" ? (
      <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 12 }} />
    ) : substep.status === "error" ? (
      <CloseCircleOutlined style={{ color: "#ff4d4f", fontSize: 12 }} />
    ) : (
      <LoadingOutlined style={{ color: "#1890ff", fontSize: 12 }} />
    );

  return (
    <div
      style={{
        padding: "8px 12px",
        background: substep.status === "completed" ? "#f6ffed" : substep.status === "error" ? "#fff2f0" : "#e6f4ff",
        borderRadius: 4,
        marginBottom: 8,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {statusIcon}
        <Text strong style={{ fontSize: 13 }}>{info.name}</Text>
        {substep.status === "running" && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            执行中...
          </Text>
        )}
      </div>
      {substep.result && substep.status === "completed" && (
        <div style={{ marginTop: 6, fontSize: 12 }}>
          {formatSubagentResult(substep.toolName, substep.result, substep.args)}
        </div>
      )}
    </div>
  );
}

// 步骤结果展示
function StepResultDisplay({ toolName, result }: { toolName: string; result: string }) {
  const maxLength = 2000;
  const truncated = result.length > maxLength ? result.slice(0, maxLength) + "\n... (已截断)" : result;

  switch (toolName) {
    case "execute_sql":
      return <DataTable data={parseTableData(result)} />;
    case "write_todos": {
      // 解析结果中的任务数量
      const match = result.match(/(\d+)\s*(?:个)?(?:任务|todo|item)/i);
      const count = match ? match[1] : "?";
      return (
        <div
          style={{
            background: "#f6ffed",
            border: "1px solid #b7eb8f",
            borderRadius: 4,
            padding: "8px 12px",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <CheckCircleOutlined style={{ color: "#52c41a" }} />
          <Text style={{ color: "#52c41a" }}>
            任务清单已更新 ({count} 个任务)
          </Text>
        </div>
      );
    }
    case "task":
      // 子代理任务结果 - 使用 markdown 渲染，支持放大查看
      return (
        <ExpandableMarkdown
          content={truncated}
          maxHeight={400}
          modalTitle="子代理执行结果"
        />
      );
    default:
      return (
        <div style={{ background: "#1a1a2e", padding: 12, borderRadius: 4, maxHeight: 200, overflow: "auto" }}>
          <pre style={{ margin: 0, fontSize: 12, color: "#e0e0e0", whiteSpace: "pre-wrap" }}>{truncated}</pre>
        </div>
      );
  }
}

// 空闲状态内容
function LiveContent({
  toolResult,
}: {
  toolResult: { toolName: string; args: Record<string, unknown>; result: string } | null;
}) {
  const { token } = theme.useToken();

  if (!toolResult) {
    return (
      <div
        className="animate-fade-in"
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          minHeight: 400,
        }}
      >
        <div
          style={{
            width: 80,
            height: 80,
            borderRadius: 20,
            background: token.colorFillTertiary,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: token.marginLG,
          }}
        >
          <ThunderboltOutlined style={{ fontSize: 40, color: token.colorTextTertiary }} />
        </div>
        <Title level={4} style={{ color: token.colorTextSecondary, marginBottom: token.marginXS }}>
          等待 AI 执行操作
        </Title>
        <Text type="secondary" style={{ maxWidth: 300, textAlign: "center" }}>
          与右侧的数据分析助手对话，这里将显示执行的具体内容和结果
        </Text>
      </div>
    );
  }

  return <ToolResultDisplay toolResult={toolResult} />;
}

// 历史内容
function HistoricalContent({ step }: { step: { index: number; toolName: string; args: Record<string, unknown>; result: string } | null }) {
  if (!step) return null;
  return <ToolResultDisplay toolResult={{ toolName: step.toolName, args: step.args, result: step.result }} />;
}

// 工具结果展示
function ToolResultDisplay({ toolResult }: { toolResult: { toolName: string; args: Record<string, unknown>; result: string } }) {
  const { toolName, args, result } = toolResult;

  switch (toolName) {
    case "execute_sql":
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Card title="SQL 查询" size="small">
            <CodeViewer code={(args.query as string) || ""} language="sql" />
          </Card>
          <Card title="查询结果" size="small">
            <DataTable data={parseTableData(result)} />
          </Card>
        </div>
      );
    case "execute_python_safe":
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Card title="Python 代码" size="small">
            <CodeViewer code={(args.code as string) || ""} language="python" />
          </Card>
          <Card title="执行输出" size="small">
            <pre style={{ background: "#1a1a2e", color: "#e0e0e0", padding: 16, borderRadius: 4, overflow: "auto", margin: 0 }}>
              {result}
            </pre>
          </Card>
        </div>
      );
    case "task":
      // 子代理任务 - 使用 markdown 渲染结果，支持放大查看
      return (
        <Card title="子代理执行结果" size="small">
          <ExpandableMarkdown
            content={result}
            maxHeight={500}
            modalTitle="子代理执行结果"
          />
        </Card>
      );
    default:
      return (
        <Card title={toolName} size="small">
          <pre style={{ background: "#fafafa", padding: 16, borderRadius: 4, overflow: "auto", margin: 0 }}>
            {result}
          </pre>
        </Card>
      );
  }
}

// 解析表格数据
function parseTableData(result: string): { columns: string[]; rows: string[][] } {
  const lines = result.trim().split("\n");
  if (lines.length === 0) return { columns: [], rows: [] };

  let dataStartIndex = 0;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith("查询结果") || line.startsWith("[已导出至")) {
      dataStartIndex = i + 1;
      continue;
    }
    if (line && !line.startsWith("查询结果") && !line.startsWith("[已导出至")) {
      dataStartIndex = i;
      break;
    }
  }

  const dataLines = lines.slice(dataStartIndex).filter((line) => {
    const trimmed = line.trim();
    return trimmed && !trimmed.startsWith("[已导出至");
  });

  if (dataLines.length === 0) return { columns: [], rows: [] };

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

  const columns = parseCSVLine(dataLines[0]);
  const rows = dataLines.slice(1).map(parseCSVLine);

  return { columns, rows };
}
