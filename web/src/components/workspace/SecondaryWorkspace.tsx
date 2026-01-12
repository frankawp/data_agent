"use client";

import { useEffect, useState } from "react";
import { useWorkspace, SecondaryContent } from "@/hooks/useWorkspaceContext";

interface SecondaryWorkspaceProps {
  content: SecondaryContent | null;
}

export function SecondaryWorkspace({ content }: SecondaryWorkspaceProps) {
  const { setActiveTab } = useWorkspace();

  if (!content) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        <p>点击左侧边栏项目查看详情</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-white p-4">
      {/* 返回按钮 */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">
          {getContentTitle(content)}
        </h2>
        <button
          onClick={() => setActiveTab("main")}
          className="rounded border px-3 py-1 text-sm text-gray-600 hover:bg-gray-50"
        >
          返回主工作区
        </button>
      </div>

      {/* 根据类型渲染内容 */}
      <ContentRenderer content={content} />
    </div>
  );
}

function getContentTitle(content: SecondaryContent): string {
  switch (content.type) {
    case "table":
      return `表结构: ${content.data.tableName as string}`;
    case "model":
      return `模型详情: ${content.data.modelId as string}`;
    case "export":
      return `文件: ${content.data.name as string}`;
    case "graph":
      return `图: ${content.data.graphId as string}`;
    default:
      return "详情";
  }
}

function ContentRenderer({ content }: { content: SecondaryContent }) {
  switch (content.type) {
    case "table":
      return <TableSchemaView tableName={content.data.tableName as string} />;
    case "model":
      return <ModelDetailView modelId={content.data.modelId as string} />;
    case "export":
      return <ExportFileView file={content.data} />;
    case "graph":
      return <GraphDetailView graphId={content.data.graphId as string} />;
    default:
      return <pre>{JSON.stringify(content.data, null, 2)}</pre>;
  }
}

function TableSchemaView({ tableName }: { tableName: string }) {
  const [schema, setSchema] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/database/tables/${tableName}`)
      .then((r) => r.json())
      .then((data) => {
        setSchema(data.schema || JSON.stringify(data, null, 2));
        setLoading(false);
      })
      .catch(() => {
        setSchema("加载失败");
        setLoading(false);
      });
  }, [tableName]);

  if (loading) {
    return <div className="text-gray-500">加载中...</div>;
  }

  return (
    <div className="rounded-lg border">
      <pre className="p-4 text-sm overflow-auto">{schema}</pre>
    </div>
  );
}

function ModelDetailView({ modelId }: { modelId: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-gray-600">模型 ID: {modelId}</p>
      <p className="text-sm text-gray-400 mt-2">
        模型详情将在训练完成后显示
      </p>
    </div>
  );
}

function ExportFileView({ file }: { file: Record<string, unknown> }) {
  const name = file.name as string;
  const size = file.size as number;

  return (
    <div className="space-y-4">
      <div className="rounded-lg border p-4">
        <p>
          <strong>文件名:</strong> {name}
        </p>
        <p>
          <strong>大小:</strong> {formatFileSize(size)}
        </p>
      </div>
      <a
        href={`/api/sessions/exports/${name}`}
        download
        className="inline-block rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
      >
        下载文件
      </a>
    </div>
  );
}

function GraphDetailView({ graphId }: { graphId: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-gray-600">图 ID: {graphId}</p>
      <p className="text-sm text-gray-400 mt-2">
        图可视化将在创建图后显示
      </p>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
