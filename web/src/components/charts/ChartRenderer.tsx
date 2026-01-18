"use client";

/**
 * 图表渲染组件
 *
 * 基于 @ant-design/charts 实现前端动态图表渲染。
 * 支持折线图、柱状图、饼图、面积图、散点图、条形图等常见图表类型。
 */

import dynamic from "next/dynamic";
import { Empty, Spin, Typography, Card } from "antd";

const { Title } = Typography;

// 动态导入图表组件，禁用 SSR（图表库依赖 DOM）
const Line = dynamic(() => import("@ant-design/charts").then((mod) => mod.Line), {
  ssr: false,
  loading: () => <ChartLoading />,
});

const Column = dynamic(() => import("@ant-design/charts").then((mod) => mod.Column), {
  ssr: false,
  loading: () => <ChartLoading />,
});

const Pie = dynamic(() => import("@ant-design/charts").then((mod) => mod.Pie), {
  ssr: false,
  loading: () => <ChartLoading />,
});

const Area = dynamic(() => import("@ant-design/charts").then((mod) => mod.Area), {
  ssr: false,
  loading: () => <ChartLoading />,
});

const Scatter = dynamic(() => import("@ant-design/charts").then((mod) => mod.Scatter), {
  ssr: false,
  loading: () => <ChartLoading />,
});

const Bar = dynamic(() => import("@ant-design/charts").then((mod) => mod.Bar), {
  ssr: false,
  loading: () => <ChartLoading />,
});

// 加载占位组件
function ChartLoading() {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: 300 }}>
      <Spin tip="加载图表..." />
    </div>
  );
}

// 支持的图表类型
export type ChartType = "line" | "column" | "pie" | "area" | "scatter" | "bar";

// 图表数据接口
export interface ChartData {
  chartType: ChartType;
  title?: string;
  data: Array<Record<string, unknown>>;
  config: {
    xField?: string;
    yField?: string;
    seriesField?: string;
    colorField?: string;
    angleField?: string;
    sizeField?: string;
    label?: Record<string, unknown>;
    legend?: Record<string, unknown> | boolean;
    tooltip?: Record<string, unknown> | boolean;
    [key: string]: unknown;
  };
}

interface ChartRendererProps {
  chartData: ChartData;
  height?: number;
  showCard?: boolean;
}

/**
 * 图表渲染器
 *
 * @param chartData - 图表数据和配置
 * @param height - 图表高度，默认 400
 * @param showCard - 是否显示卡片容器，默认 true
 */
export function ChartRenderer({ chartData, height = 400, showCard = true }: ChartRendererProps) {
  const { chartType, data, config, title } = chartData;

  // 数据为空时显示空状态
  if (!data || data.length === 0) {
    return <Empty description="暂无数据" />;
  }

  // 通用配置
  const commonConfig = {
    data,
    height,
    autoFit: true,
    animation: {
      appear: {
        animation: "fade-in",
        duration: 300,
      },
    },
    ...config,
  };

  // 根据图表类型渲染对应组件
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderChart = (): React.ReactNode => {
    // 使用 any 类型以支持动态配置
    const chartProps = commonConfig as Record<string, unknown>;

    switch (chartType) {
      case "line":
        return (
          <Line
            {...chartProps}
            xField={config.xField || "x"}
            yField={config.yField || "y"}
            colorField={config.seriesField}
          />
        );

      case "column":
        return (
          <Column
            {...chartProps}
            xField={config.xField || "x"}
            yField={config.yField || "y"}
            colorField={config.seriesField}
          />
        );

      case "bar":
        return (
          <Bar
            {...chartProps}
            xField={config.yField || "y"}
            yField={config.xField || "x"}
            colorField={config.seriesField}
          />
        );

      case "pie":
        return (
          <Pie
            {...chartProps}
            angleField={config.angleField || "value"}
            colorField={config.colorField || "type"}
          />
        );

      case "area":
        return (
          <Area
            {...chartProps}
            xField={config.xField || "x"}
            yField={config.yField || "y"}
            colorField={config.seriesField}
          />
        );

      case "scatter":
        return (
          <Scatter
            {...chartProps}
            xField={config.xField || "x"}
            yField={config.yField || "y"}
            colorField={config.colorField}
            sizeField={config.sizeField}
          />
        );

      default:
        return <Empty description={`不支持的图表类型: ${chartType}`} />;
    }
  };

  // 根据是否需要卡片容器返回不同结构
  if (showCard) {
    return (
      <Card
        size="small"
        title={title ? <Title level={5} style={{ margin: 0 }}>{title}</Title> : undefined}
        styles={{ body: { padding: title ? 16 : 12 } }}
      >
        {renderChart()}
      </Card>
    );
  }

  return (
    <div>
      {title && (
        <Title level={5} style={{ marginBottom: 12 }}>
          {title}
        </Title>
      )}
      {renderChart()}
    </div>
  );
}

/**
 * 从后端响应解析图表数据
 *
 * 后端应返回如下格式：
 * {
 *   "chartType": "line",
 *   "title": "销售趋势",
 *   "data": [{ "month": "1月", "sales": 1200 }, ...],
 *   "config": { "xField": "month", "yField": "sales" }
 * }
 */
export function parseChartData(response: unknown): ChartData | null {
  if (!response || typeof response !== "object") {
    return null;
  }

  const obj = response as Record<string, unknown>;

  if (!obj.chartType || !obj.data || !Array.isArray(obj.data)) {
    return null;
  }

  return {
    chartType: obj.chartType as ChartType,
    title: obj.title as string | undefined,
    data: obj.data as Array<Record<string, unknown>>,
    config: (obj.config as ChartData["config"]) || {},
  };
}

export default ChartRenderer;
