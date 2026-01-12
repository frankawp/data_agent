"use client";

interface DataTableProps {
  data: {
    columns: string[];
    rows: string[][];
  };
}

export function DataTable({ data }: DataTableProps) {
  const { columns, rows } = data;

  if (columns.length === 0) {
    return <div className="text-gray-500">无数据</div>;
  }

  return (
    <div className="overflow-auto rounded-lg border">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col, i) => (
              <th
                key={i}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              {row.map((cell, j) => (
                <td
                  key={j}
                  className="px-4 py-2 text-sm text-gray-900 max-w-xs truncate"
                  title={cell}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 0 && (
        <div className="border-t bg-gray-50 px-4 py-2 text-xs text-gray-500">
          共 {rows.length} 行
        </div>
      )}
    </div>
  );
}
