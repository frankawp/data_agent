"use client";

/**
 * Tool UI 注册表
 *
 * 注册所有 Assistant UI 工具组件。
 */

import { makeAssistantToolUI } from "@assistant-ui/react";
import { PlanConfirmationTool } from "./PlanConfirmationTool";

// SQL 查询工具 UI
export const ExecuteSQLTool = makeAssistantToolUI<
  { query: string; database?: string },
  string
>({
  toolName: "execute_sql",
  render: ({ args, result, status }) => {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span className="text-lg">🗃️</span>
          <span className="font-medium">SQL 查询</span>
          {status.type === "running" && (
            <span className="animate-pulse text-blue-500">执行中...</span>
          )}
        </div>

        {/* SQL 代码 */}
        <pre className="mt-2 overflow-x-auto rounded bg-gray-50 p-2 text-xs text-gray-800">
          {args.query}
        </pre>

        {/* 结果 */}
        {result && (
          <div className="mt-2 border-t pt-2">
            <p className="text-xs text-gray-500">结果:</p>
            <pre className="mt-1 max-h-40 overflow-auto text-xs text-gray-700">
              {result}
            </pre>
          </div>
        )}
      </div>
    );
  },
});

// Python 执行工具 UI
export const ExecutePythonTool = makeAssistantToolUI<
  { code: string; timeout?: number },
  string
>({
  toolName: "execute_python_safe",
  render: ({ args, result, status }) => {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span className="text-lg">🐍</span>
          <span className="font-medium">Python 分析</span>
          {status.type === "running" && (
            <span className="animate-pulse text-blue-500">执行中...</span>
          )}
        </div>

        {/* Python 代码 */}
        <pre className="mt-2 max-h-32 overflow-auto rounded bg-gray-900 p-2 text-xs text-green-400">
          {args.code}
        </pre>

        {/* 结果 */}
        {result && (
          <div className="mt-2 border-t pt-2">
            <p className="text-xs text-gray-500">输出:</p>
            <pre className="mt-1 max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs text-gray-700">
              {result}
            </pre>
          </div>
        )}
      </div>
    );
  },
});

// 列出表工具 UI
export const ListTablesTool = makeAssistantToolUI<Record<string, never>, string>({
  toolName: "list_tables",
  render: ({ result, status }) => {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span className="text-lg">📋</span>
          <span className="font-medium">获取表列表</span>
          {status.type === "running" && (
            <span className="animate-pulse text-blue-500">查询中...</span>
          )}
        </div>

        {result && (
          <div className="mt-2">
            <pre className="max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs text-gray-700">
              {result}
            </pre>
          </div>
        )}
      </div>
    );
  },
});

// 模型训练工具 UI
export const TrainModelTool = makeAssistantToolUI<
  {
    data_json: string;
    target_column: string;
    model_type: string;
    model_id?: string;
  },
  string
>({
  toolName: "train_model",
  render: ({ args, result, status }) => {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span className="text-lg">🤖</span>
          <span className="font-medium">训练模型</span>
          {status.type === "running" && (
            <span className="animate-pulse text-blue-500">训练中...</span>
          )}
        </div>

        <div className="mt-2 space-y-1 text-xs text-gray-600">
          <p>
            <span className="text-gray-400">模型类型:</span> {args.model_type}
          </p>
          <p>
            <span className="text-gray-400">目标列:</span> {args.target_column}
          </p>
          {args.model_id && (
            <p>
              <span className="text-gray-400">模型 ID:</span> {args.model_id}
            </p>
          )}
        </div>

        {result && (
          <div className="mt-2 border-t pt-2">
            <pre className="max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs text-gray-700">
              {result}
            </pre>
          </div>
        )}
      </div>
    );
  },
});

// 导出所有工具组件
export const ToolUIComponents = {
  PlanConfirmationTool,
  ExecuteSQLTool,
  ExecutePythonTool,
  ListTablesTool,
  TrainModelTool,
};

// 工具注册组件 - 放在 AssistantProvider 内部使用
export function RegisterToolUIs() {
  return (
    <>
      <PlanConfirmationTool />
      <ExecuteSQLTool />
      <ExecutePythonTool />
      <ListTablesTool />
      <TrainModelTool />
    </>
  );
}

export default RegisterToolUIs;
