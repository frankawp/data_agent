"use client";

/**
 * 数据库连接配置组件
 *
 * 允许用户配置 MySQL 数据库连接，支持：
 * - 输入连接参数（主机、端口、用户、密码、数据库名）
 * - 测试连接
 * - 保存配置
 */

import { useState, useEffect } from "react";
import {
  Form,
  Input,
  InputNumber,
  Button,
  Space,
  Alert,
  Typography,
  theme,
  Collapse,
  Tag,
  Tooltip,
} from "antd";
import {
  DatabaseOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  SettingOutlined,
  DisconnectOutlined,
} from "@ant-design/icons";
import { useSession } from "@/providers/SessionProvider";

const { Text } = Typography;

interface DatabaseConfigProps {
  /** 配置成功后的回调 */
  onConfigured?: () => void;
  /** 是否默认展开配置表单 */
  defaultExpanded?: boolean;
}

interface DbConfig {
  host: string;
  port: number;
  user: string;
  database: string;
}

export function DatabaseConfig({ onConfigured, defaultExpanded = false }: DatabaseConfigProps) {
  const [form] = Form.useForm();
  const { sessionId } = useSession();
  const { token } = theme.useToken();

  // 状态
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [configured, setConfigured] = useState(false);
  const [currentConfig, setCurrentConfig] = useState<DbConfig | null>(null);
  const [expanded, setExpanded] = useState(defaultExpanded);

  // 加载当前配置状态
  useEffect(() => {
    if (!sessionId) return;

    fetch(`/api/database/config?session_id=${sessionId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.configured && data.config) {
          setConfigured(true);
          setCurrentConfig(data.config);
        } else {
          setConfigured(false);
          setCurrentConfig(null);
        }
      })
      .catch(() => {
        setConfigured(false);
      });
  }, [sessionId, defaultExpanded]);

  // 测试连接
  const handleTest = async () => {
    try {
      await form.validateFields();
      const values = form.getFieldsValue();

      setTesting(true);
      setTestResult(null);

      const res = await fetch("/api/database/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });

      const data = await res.json();
      setTestResult({
        success: data.success,
        message: data.message,
      });
    } catch {
      // 表单验证失败
    } finally {
      setTesting(false);
    }
  };

  // 保存配置
  const handleSave = async () => {
    try {
      await form.validateFields();
      const values = form.getFieldsValue();

      setLoading(true);

      const res = await fetch(`/api/database/config?session_id=${sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });

      const data = await res.json();

      if (data.success) {
        setConfigured(true);
        setCurrentConfig(data.config);
        setExpanded(false);
        setTestResult(null);
        onConfigured?.();
      } else {
        setTestResult({
          success: false,
          message: data.message || "保存失败",
        });
      }
    } catch {
      // 表单验证失败
    } finally {
      setLoading(false);
    }
  };

  // 清除配置
  const handleClear = async () => {
    try {
      await fetch(`/api/database/config?session_id=${sessionId}`, {
        method: "DELETE",
      });
      setConfigured(false);
      setCurrentConfig(null);
      setExpanded(true);
      form.resetFields();
      // 通知父组件刷新表列表
      onConfigured?.();
    } catch {
      // 静默处理
    }
  };

  // 已配置状态显示
  if (configured && currentConfig && !expanded) {
    return (
      <div
        style={{
          padding: `${token.paddingSM}px ${token.padding}px`,
          background: token.colorSuccessBg,
          borderRadius: token.borderRadius,
          border: `1px solid ${token.colorSuccessBorder}`,
          marginBottom: token.marginSM,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Space size={8}>
            <CheckCircleOutlined style={{ color: token.colorSuccess }} />
            <Text strong style={{ fontSize: 13 }}>
              {currentConfig.database}
            </Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              @{currentConfig.host}:{currentConfig.port}
            </Text>
          </Space>
          <Space size={4}>
            <Tooltip title="修改配置" color="rgba(0, 0, 0, 0.85)">
              <Button
                type="text"
                size="small"
                icon={<SettingOutlined />}
                onClick={() => {
                  // 填充当前配置到表单
                  form.setFieldsValue({
                    host: currentConfig.host,
                    port: currentConfig.port,
                    user: currentConfig.user,
                    database: currentConfig.database,
                    password: "", // 密码不回显
                  });
                  setExpanded(true);
                }}
              />
            </Tooltip>
            <Tooltip title="断开连接" color="rgba(0, 0, 0, 0.85)">
              <Button
                type="text"
                size="small"
                danger
                icon={<DisconnectOutlined />}
                onClick={handleClear}
              />
            </Tooltip>
          </Space>
        </div>
      </div>
    );
  }

  return (
    <Collapse
      activeKey={expanded ? ["config"] : []}
      onChange={(keys) => setExpanded(keys.includes("config"))}
      bordered={false}
      style={{
        background: "transparent",
        marginBottom: token.marginSM,
      }}
      items={[
        {
          key: "config",
          label: (
            <Space>
              <DatabaseOutlined style={{ color: token.colorPrimary }} />
              <Text strong style={{ fontSize: 13 }}>
                配置数据库连接
              </Text>
              {!configured && (
                <Tag color="warning" style={{ marginLeft: 8 }}>
                  未配置
                </Tag>
              )}
            </Space>
          ),
          children: (
            <Form
              form={form}
              layout="vertical"
              size="small"
              initialValues={{
                host: "localhost",
                port: 3306,
                user: "root",
                database: "",
                password: "",
              }}
            >
              <Form.Item
                label="主机地址"
                name="host"
                rules={[{ required: true, message: "请输入主机地址" }]}
              >
                <Input placeholder="localhost 或 IP 地址" />
              </Form.Item>

              <Form.Item
                label="端口"
                name="port"
                rules={[{ required: true, message: "请输入端口" }]}
              >
                <InputNumber
                  min={1}
                  max={65535}
                  style={{ width: "100%" }}
                  placeholder="3306"
                />
              </Form.Item>

              <Form.Item
                label="用户名"
                name="user"
                rules={[{ required: true, message: "请输入用户名" }]}
              >
                <Input placeholder="数据库用户名" />
              </Form.Item>

              <Form.Item
                label="密码"
                name="password"
                rules={[{ required: true, message: "请输入密码" }]}
              >
                <Input.Password placeholder="数据库密码" />
              </Form.Item>

              <Form.Item
                label="数据库名"
                name="database"
                rules={[{ required: true, message: "请输入数据库名" }]}
              >
                <Input placeholder="要连接的数据库" />
              </Form.Item>

              {/* 测试结果 */}
              {testResult && (
                <Alert
                  type={testResult.success ? "success" : "error"}
                  message={testResult.message}
                  showIcon
                  icon={testResult.success ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                  style={{ marginBottom: token.marginSM }}
                />
              )}

              {/* 操作按钮 */}
              <Form.Item style={{ marginBottom: 0 }}>
                <Space style={{ width: "100%", justifyContent: "flex-end" }}>
                  <Button onClick={handleTest} disabled={testing || loading}>
                    {testing ? <LoadingOutlined /> : null}
                    测试连接
                  </Button>
                  <Button
                    type="primary"
                    onClick={handleSave}
                    disabled={loading || testing}
                  >
                    {loading ? <LoadingOutlined /> : null}
                    保存配置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          ),
        },
      ]}
    />
  );
}
