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
} from "@ant-design/icons";
import { useWorkspace, StreamingStep, SubagentStep } from "@/hooks/useWorkspaceContext";
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

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#fff" }}>
      {/* 标题栏 */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 16px",
          borderBottom: "1px solid #f0f0f0",
          background: "#fafafa",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <CodeOutlined style={{ fontSize: 16, color: "#2563eb" }} />
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
        style={{ flex: 1, overflow: "auto", padding: 16 }}
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
          style={{
            position: "absolute",
            bottom: 24,
            left: "50%",
            transform: "translateX(-50%)",
            borderRadius: 20,
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
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

// 流式执行内容
function StreamingContent({ steps, isStreaming }: { steps: StreamingStep[]; isStreaming: boolean }) {
  if (steps.length === 0 && isStreaming) {
    return (
      <Empty
        image={<Spin size="large" />}
        description={
          <Text type="secondary" style={{ fontSize: 16 }}>
            AI 正在分析任务...
          </Text>
        }
        style={{ marginTop: 100 }}
      />
    );
  }

  const completedCount = steps.filter((s) => s.status === "completed").length;

  return (
    <div>
      {/* 进度概览 */}
      <Card size="small" style={{ marginBottom: 16 }}>
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
              <CheckCircleOutlined style={{ color: "#52c41a" }} />
            ) : step.status === "error" ? (
              <CloseCircleOutlined style={{ color: "#ff4d4f" }} />
            ) : (
              <LoadingOutlined style={{ color: "#1890ff" }} />
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
function StepCard({ step, info }: { step: StreamingStep; info: { name: string; icon: React.ReactNode; color: string } }) {
  const borderColor =
    step.status === "completed" ? "#52c41a" : step.status === "error" ? "#ff4d4f" : "#1890ff";

  return (
    <Card
      size="small"
      style={{ borderLeft: `3px solid ${borderColor}`, marginBottom: 8 }}
      styles={{ body: { padding: "12px 16px" } }}
    >
      {/* 步骤头部 */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
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
        <div style={{ marginTop: 12, marginLeft: 16, borderLeft: "2px solid #e6f4ff", paddingLeft: 12 }}>
          <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: 8 }}>
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
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #f0f0f0" }}>
          <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: 8 }}>
            执行结果:
          </Text>
          <StepResultDisplay toolName={step.toolName} result={step.result} />
        </div>
      )}
    </Card>
  );
}

// 简单 Markdown 渲染组件
function SimpleMarkdown({ text }: { text: string }) {
  // 将文本按段落分割
  const paragraphs = text.split(/\n\n+/);

  return (
    <div style={{ fontSize: 13, lineHeight: 1.8 }}>
      {paragraphs.map((paragraph, idx) => {
        // 检查是否是有序列表 (1. 2. 3. ...)
        if (/^\d+\.\s/.test(paragraph.trim())) {
          const items = paragraph.split(/\n/).filter((line) => line.trim());
          return (
            <ol key={idx} style={{ margin: "8px 0", paddingLeft: 24 }}>
              {items.map((item, i) => (
                <li key={i} style={{ margin: "4px 0" }}>
                  <MarkdownText text={item.replace(/^\d+\.\s*/, "")} />
                </li>
              ))}
            </ol>
          );
        }

        // 检查是否是无序列表 (- 或 *)
        if (/^[-*]\s/.test(paragraph.trim())) {
          const items = paragraph.split(/\n/).filter((line) => line.trim());
          return (
            <ul key={idx} style={{ margin: "8px 0", paddingLeft: 24 }}>
              {items.map((item, i) => (
                <li key={i} style={{ margin: "4px 0" }}>
                  <MarkdownText text={item.replace(/^[-*]\s*/, "")} />
                </li>
              ))}
            </ul>
          );
        }

        // 普通段落
        return (
          <p key={idx} style={{ margin: "6px 0" }}>
            <MarkdownText text={paragraph} />
          </p>
        );
      })}
    </div>
  );
}

// 处理行内 markdown 格式（加粗、斜体）
function MarkdownText({ text }: { text: string }) {
  // 匹配 **加粗** 和 *斜体*
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);

  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={i} style={{ color: "#389e0d", fontWeight: 600 }}>
              {part.slice(2, -2)}
            </strong>
          );
        }
        if (part.startsWith("*") && part.endsWith("*")) {
          return <em key={i}>{part.slice(1, -1)}</em>;
        }
        return <span key={i}>{part}</span>;
      })}
    </>
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
      // Python 执行 - 简化显示
      const lines = result.split("\n").filter(Boolean);
      if (lines.length > 0) {
        return <Text type="secondary">{lines[0].slice(0, 80)}{lines[0].length > 80 || lines.length > 1 ? "..." : ""}</Text>;
      }
      return <Text type="secondary">执行完成</Text>;
    }

    case "ls": {
      // 文件列表 - 显示路径和内容
      const path = args?.path ? String(args.path) : "";
      return (
        <div>
          {path && (
            <Text type="secondary" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>
              📁 {path}
            </Text>
          )}
          <pre style={{
            margin: 0,
            fontSize: 11,
            fontFamily: "monospace",
            background: "#f5f5f5",
            padding: 8,
            borderRadius: 4,
            maxHeight: 100,
            overflow: "auto",
            whiteSpace: "pre-wrap",
            wordBreak: "break-all"
          }}>
            {result.length > 300 ? result.slice(0, 300) + "\n..." : result}
          </pre>
        </div>
      );
    }

    case "read_file": {
      // 读取文件 - 根据文件类型渲染内容
      const filePath = args?.path ? String(args.path) : (args?.file_path ? String(args.file_path) : "");
      const filename = filePath.split("/").pop() || "file.txt";
      return (
        <div>
          {filePath && (
            <Tag color="blue" style={{ marginBottom: 6 }}>
              📄 {filePath}
            </Tag>
          )}
          <FileContentRenderer
            filename={filename}
            content={result}
            compact
            maxHeight={150}
          />
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
      return (
        <div style={{ background: "#fafafa", padding: 12, borderRadius: 4, maxHeight: 300, overflow: "auto" }}>
          <pre style={{ margin: 0, fontSize: 13, whiteSpace: "pre-wrap" }}>{truncated}</pre>
        </div>
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
function LiveContent({ toolResult }: { toolResult: { toolName: string; args: Record<string, unknown>; result: string } | null }) {
  if (!toolResult) {
    return (
      <Empty
        image={<CodeOutlined style={{ fontSize: 64, color: "#d9d9d9" }} />}
        description={
          <div style={{ textAlign: "center" }}>
            <Title level={4} style={{ color: "#8c8c8c" }}>
              等待 AI 执行操作
            </Title>
            <Text type="secondary">与右侧的数据分析助手对话，这里将显示执行的具体内容</Text>
          </div>
        }
        style={{ marginTop: 100 }}
      />
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
