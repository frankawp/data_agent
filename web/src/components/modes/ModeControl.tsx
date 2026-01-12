"use client";

import { useEffect, useState } from "react";

interface Modes {
  plan: string;
  auto: boolean;
  safe: boolean;
  verbose: boolean;
  preview: string;
  export: boolean;
}

export function ModeControl() {
  const [modes, setModes] = useState<Modes>({
    plan: "off",
    auto: true,
    safe: true,
    verbose: false,
    preview: "50",
    export: false,
  });
  const [loading, setLoading] = useState(true);

  // 加载模式状态
  useEffect(() => {
    fetch("/api/modes")
      .then((r) => r.json())
      .then((data) => {
        if (data.modes) {
          setModes(data.modes);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // 更新模式
  const updateMode = async (key: string, value: string | boolean) => {
    const stringValue = typeof value === "boolean" ? (value ? "on" : "off") : value;

    try {
      const response = await fetch(`/api/modes/${key}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: stringValue }),
      });

      if (response.ok) {
        const data = await response.json();
        setModes((prev) => ({
          ...prev,
          [key]: typeof value === "boolean" ? value : data.value,
        }));
      }
    } catch (error) {
      console.error("更新模式失败:", error);
    }
  };

  if (loading) {
    return <div className="text-sm text-gray-500">加载中...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Plan Mode - 三态选择 */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium text-gray-700">计划模式</span>
          <p className="text-xs text-gray-500">控制任务规划行为</p>
        </div>
        <select
          value={modes.plan}
          onChange={(e) => updateMode("plan", e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        >
          <option value="off">关闭</option>
          <option value="on">开启</option>
          <option value="auto">自动</option>
        </select>
      </div>

      {/* Auto Execute - 开关 */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium text-gray-700">自动执行</span>
          <p className="text-xs text-gray-500">自动执行工具调用</p>
        </div>
        <ToggleSwitch
          checked={modes.auto}
          onChange={(v) => updateMode("auto", v)}
        />
      </div>

      {/* Safe Mode - 开关 */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium text-gray-700">安全模式</span>
          <p className="text-xs text-gray-500">限制危险 SQL 操作</p>
        </div>
        <ToggleSwitch
          checked={modes.safe}
          onChange={(v) => updateMode("safe", v)}
        />
      </div>

      {/* Verbose - 开关 */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium text-gray-700">详细输出</span>
          <p className="text-xs text-gray-500">显示详细思考过程</p>
        </div>
        <ToggleSwitch
          checked={modes.verbose}
          onChange={(v) => updateMode("verbose", v)}
        />
      </div>

      {/* Preview Limit - 选择 */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium text-gray-700">预览行数</span>
          <p className="text-xs text-gray-500">数据预览的最大行数</p>
        </div>
        <select
          value={modes.preview}
          onChange={(e) => updateMode("preview", e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        >
          <option value="10">10 行</option>
          <option value="50">50 行</option>
          <option value="100">100 行</option>
          <option value="all">全部</option>
        </select>
      </div>

      {/* Export Mode - 开关 */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium text-gray-700">自动导出</span>
          <p className="text-xs text-gray-500">自动保存结果到文件</p>
        </div>
        <ToggleSwitch
          checked={modes.export}
          onChange={(v) => updateMode("export", v)}
        />
      </div>
    </div>
  );
}

interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function ToggleSwitch({ checked, onChange }: ToggleSwitchProps) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? "bg-blue-600" : "bg-gray-200"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          checked ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}
