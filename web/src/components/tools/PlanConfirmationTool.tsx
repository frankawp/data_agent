"use client";

/**
 * Plan Mode 确认组件
 *
 * 在聊天界面内联显示执行计划，用户可以确认或取消。
 */

import { makeAssistantToolUI } from "@assistant-ui/react";

// 计划步骤类型
interface PlanStep {
  index: number;
  description: string;
  tool_hint?: string;
}

// 计划参数类型
interface PlanArgs {
  plan_id: string;
  goal: string;
  steps: PlanStep[];
  complexity: string;
  estimated_tools: string[];
}

// 确认结果类型
interface PlanResult {
  approved: boolean;
  plan_id: string;
}

export const PlanConfirmationTool = makeAssistantToolUI<PlanArgs, PlanResult>({
  toolName: "plan_confirmation",
  render: ({ args, result, addResult }) => {
    // 已有结果 - 显示确认状态
    if (result) {
      return (
        <div
          className={`rounded-lg p-3 ${
            result.approved
              ? "bg-green-50 text-green-800"
              : "bg-red-50 text-red-800"
          }`}
        >
          {result.approved ? (
            <div className="flex items-center gap-2">
              <span className="text-lg">✅</span>
              <span className="font-medium">计划已确认，正在执行...</span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-lg">❌</span>
              <span className="font-medium">计划已取消</span>
            </div>
          )}
        </div>
      );
    }

    // 等待确认 - 显示计划详情
    return (
      <div className="rounded-lg border-2 border-amber-400 bg-amber-50 p-4">
        {/* 标题 */}
        <div className="flex items-center gap-2 text-amber-800">
          <span className="text-xl">📋</span>
          <h4 className="font-bold">执行计划确认</h4>
          {args.complexity && (
            <span className="rounded bg-amber-200 px-2 py-0.5 text-xs">
              {args.complexity === "complex" ? "复杂" : "中等"}
            </span>
          )}
        </div>

        {/* 目标 */}
        <p className="mt-2 text-gray-700">{args.goal}</p>

        {/* 步骤列表 */}
        <div className="mt-3 space-y-2">
          {args.steps.map((step, i) => (
            <div
              key={step.index || i}
              className="flex items-start gap-2 rounded bg-white p-2 text-sm"
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-200 text-amber-800">
                {step.index || i + 1}
              </span>
              <div className="flex-1">
                <span className="text-gray-700">{step.description}</span>
                {step.tool_hint && (
                  <span className="ml-2 text-xs text-gray-400">
                    ({step.tool_hint})
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* 预计使用的工具 */}
        {args.estimated_tools && args.estimated_tools.length > 0 && (
          <div className="mt-3 text-xs text-gray-500">
            预计使用：{args.estimated_tools.join(", ")}
          </div>
        )}

        {/* 操作按钮 */}
        <div className="mt-4 flex gap-2">
          <button
            onClick={() =>
              addResult({ approved: true, plan_id: args.plan_id })
            }
            className="flex-1 rounded-lg bg-green-500 px-4 py-2 font-medium text-white transition-colors hover:bg-green-600"
          >
            ✓ 确认执行
          </button>
          <button
            onClick={() =>
              addResult({ approved: false, plan_id: args.plan_id })
            }
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 font-medium text-gray-600 transition-colors hover:bg-gray-50"
          >
            取消
          </button>
        </div>
      </div>
    );
  },
});

export default PlanConfirmationTool;
