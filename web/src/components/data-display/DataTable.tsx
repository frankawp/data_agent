"use client";

import { Table, Empty, Typography, theme, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { TableOutlined } from "@ant-design/icons";

const { Text } = Typography;

interface DataTableProps {
  data: {
    columns: string[];
    rows: string[][];
  };
  /** 最大显示行数，超出时截断 */
  maxRows?: number;
  /** 紧凑模式，用于子代理步骤展示 */
  compact?: boolean;
}

export function DataTable({ data, maxRows, compact }: DataTableProps) {
  const { token } = theme.useToken();
  const { columns: columnNames, rows } = data;

  if (columnNames.length === 0) {
    return (
      <Empty
        description="无数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        style={{ padding: token.paddingLG }}
      />
    );
  }

  // 限制行数
  const displayRows = maxRows ? rows.slice(0, maxRows) : rows;
  const hasMore = maxRows && rows.length > maxRows;

  // 构建 Ant Design Table 列配置
  const columns: ColumnsType<Record<string, string>> = columnNames.map((col, index) => ({
    title: (
      <Text strong style={{ fontSize: compact ? 12 : 13 }}>
        {col}
      </Text>
    ),
    dataIndex: `col_${index}`,
    key: `col_${index}`,
    ellipsis: true,
    width: compact ? 100 : 150,
    render: (text: string) => (
      <Text
        ellipsis={{ tooltip: text }}
        style={{ maxWidth: compact ? 90 : 140, fontSize: compact ? 12 : 13 }}
      >
        {text}
      </Text>
    ),
  }));

  // 转换行数据为对象格式
  const dataSource = displayRows.map((row, rowIndex) => {
    const record: Record<string, string> = { key: `row_${rowIndex}` };
    row.forEach((cell, colIndex) => {
      record[`col_${colIndex}`] = cell;
    });
    return record;
  });

  return (
    <div className="animate-fade-in">
      {/* 表格信息 */}
      {!compact && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: token.marginSM,
          }}
        >
          <Tag icon={<TableOutlined />} color="blue">
            {rows.length} 行 x {columnNames.length} 列
          </Tag>
        </div>
      )}

      <Table
        columns={columns}
        dataSource={dataSource}
        size="small"
        scroll={{ x: "max-content" }}
        pagination={
          compact
            ? false
            : {
                size: "small",
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 行`,
                pageSizeOptions: ["10", "20", "50", "100"],
                defaultPageSize: 20,
              }
        }
        bordered
        style={{
          borderRadius: token.borderRadius,
          overflow: "hidden",
        }}
        rowClassName={(_, index) => (index % 2 === 0 ? "" : "table-row-striped")}
      />

      {hasMore && (
        <Text
          type="secondary"
          style={{
            fontSize: 12,
            display: "block",
            marginTop: token.marginXS,
            textAlign: "right",
          }}
        >
          显示前 {maxRows} 行，共 {rows.length} 行
        </Text>
      )}

      {/* 斑马纹样式 */}
      <style jsx global>{`
        .table-row-striped {
          background-color: ${token.colorFillTertiary};
        }
        .table-row-striped:hover > td {
          background-color: ${token.colorFillSecondary} !important;
        }
      `}</style>
    </div>
  );
}
