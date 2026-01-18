"use client";

import { useEffect, useState } from "react";
import { Form, Switch, Select, Spin, Typography } from "antd";

const { Text } = Typography;

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
    return (
      <div style={{ textAlign: "center", padding: "20px 0" }}>
        <Spin size="small" />
      </div>
    );
  }

  return (
    <Form layout="vertical" size="small">
      {/* Plan Mode - 三态选择 */}
      <Form.Item
        label={<Text strong>计划模式</Text>}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>控制任务规划行为</Text>}
        style={{ marginBottom: 16 }}
      >
        <Select
          value={modes.plan}
          onChange={(v) => updateMode("plan", v)}
          options={[
            { value: "off", label: "关闭" },
            { value: "on", label: "开启" },
            { value: "auto", label: "自动" },
          ]}
          style={{ width: 100 }}
        />
      </Form.Item>

      {/* Auto Execute - 开关 */}
      <Form.Item
        label={<Text strong>自动执行</Text>}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>自动执行工具调用</Text>}
        style={{ marginBottom: 16 }}
      >
        <Switch checked={modes.auto} onChange={(v) => updateMode("auto", v)} />
      </Form.Item>

      {/* Safe Mode - 开关 */}
      <Form.Item
        label={<Text strong>安全模式</Text>}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>限制危险 SQL 操作</Text>}
        style={{ marginBottom: 16 }}
      >
        <Switch checked={modes.safe} onChange={(v) => updateMode("safe", v)} />
      </Form.Item>

      {/* Verbose - 开关 */}
      <Form.Item
        label={<Text strong>详细输出</Text>}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>显示详细思考过程</Text>}
        style={{ marginBottom: 16 }}
      >
        <Switch checked={modes.verbose} onChange={(v) => updateMode("verbose", v)} />
      </Form.Item>

      {/* Preview Limit - 选择 */}
      <Form.Item
        label={<Text strong>预览行数</Text>}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>数据预览的最大行数</Text>}
        style={{ marginBottom: 16 }}
      >
        <Select
          value={modes.preview}
          onChange={(v) => updateMode("preview", v)}
          options={[
            { value: "10", label: "10 行" },
            { value: "50", label: "50 行" },
            { value: "100", label: "100 行" },
            { value: "all", label: "全部" },
          ]}
          style={{ width: 100 }}
        />
      </Form.Item>

      {/* Export Mode - 开关 */}
      <Form.Item
        label={<Text strong>自动导出</Text>}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>自动保存结果到文件</Text>}
        style={{ marginBottom: 0 }}
      >
        <Switch checked={modes.export} onChange={(v) => updateMode("export", v)} />
      </Form.Item>
    </Form>
  );
}
