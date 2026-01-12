"use client";

import { useState, useEffect } from "react";
import { useWorkspace } from "@/hooks/useWorkspaceContext";

interface SidebarProps {
  className?: string;
}

interface TableInfo {
  name: string;
  type: "table" | "view";
}

interface ModelInfo {
  id: string;
  type: string;
}

interface ExportFile {
  name: string;
  path: string;
  size: number;
}

export function Sidebar({ className }: SidebarProps) {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [exports, setExports] = useState<ExportFile[]>([]);
  const [expandedSections, setExpandedSections] = useState<string[]>([
    "database",
  ]);
  const { setSecondaryContent, setActiveTab } = useWorkspace();

  // 加载数据库表
  useEffect(() => {
    fetch("/api/database/tables")
      .then((r) => r.json())
      .then((data) => {
        if (data.tables) {
          // 解析表列表
          const tableList: TableInfo[] = [];
          if (typeof data.tables === "string") {
            // 如果是字符串格式，解析它
            // 后端返回格式: "数据库中的表:\n- table1\n- table2"
            const lines = data.tables.split("\n");
            lines.forEach((line: string) => {
              const trimmed = line.trim();
              // 跳过标题行和空行，解析 "- tablename" 格式
              if (trimmed && trimmed.startsWith("- ")) {
                const name = trimmed.slice(2); // 去掉 "- " 前缀
                tableList.push({ name, type: "table" });
              }
            });
          }
          setTables(tableList);
        }
      })
      .catch(() => {});
  }, []);

  // 加载导出文件
  useEffect(() => {
    fetch("/api/sessions/exports")
      .then((r) => r.json())
      .then((data) => {
        if (data.files) {
          setExports(data.files);
        }
      })
      .catch(() => {});
  }, []);

  const toggleSection = (section: string) => {
    setExpandedSections((prev) =>
      prev.includes(section)
        ? prev.filter((s) => s !== section)
        : [...prev, section]
    );
  };

  const handleTableClick = (tableName: string) => {
    setSecondaryContent({
      type: "table",
      data: { tableName },
    });
    setActiveTab("secondary");
  };

  const handleModelClick = (modelId: string) => {
    setSecondaryContent({
      type: "model",
      data: { modelId },
    });
    setActiveTab("secondary");
  };

  const handleExportClick = (file: ExportFile) => {
    setSecondaryContent({
      type: "export",
      data: { name: file.name, path: file.path, size: file.size },
    });
    setActiveTab("secondary");
  };

  return (
    <aside className={`flex flex-col overflow-hidden ${className}`}>
      <div className="flex-1 overflow-y-auto p-3">
        {/* 数据库浏览器 */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection("database")}
            className="flex w-full items-center justify-between py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <span className="flex items-center gap-2">
              <span>📊</span>
              数据库浏览器
            </span>
            <span>{expandedSections.includes("database") ? "▼" : "▶"}</span>
          </button>
          {expandedSections.includes("database") && (
            <div className="ml-4 space-y-1">
              {tables.length === 0 ? (
                <p className="text-xs text-gray-400">未连接数据库</p>
              ) : (
                tables.map((table) => (
                  <button
                    key={table.name}
                    onClick={() => handleTableClick(table.name)}
                    className="flex w-full items-center gap-2 rounded px-2 py-1 text-sm text-gray-600 hover:bg-gray-100"
                  >
                    <span>{table.type === "view" ? "👁" : "📋"}</span>
                    {table.name}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* 已训练模型 */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection("models")}
            className="flex w-full items-center justify-between py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <span className="flex items-center gap-2">
              <span>🧠</span>
              已训练模型
            </span>
            <span>{expandedSections.includes("models") ? "▼" : "▶"}</span>
          </button>
          {expandedSections.includes("models") && (
            <div className="ml-4 space-y-1">
              {models.length === 0 ? (
                <p className="text-xs text-gray-400">暂无模型</p>
              ) : (
                models.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => handleModelClick(model.id)}
                    className="flex w-full items-center gap-2 rounded px-2 py-1 text-sm text-gray-600 hover:bg-gray-100"
                  >
                    <span>📈</span>
                    {model.id}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* 导出文件 */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection("exports")}
            className="flex w-full items-center justify-between py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <span className="flex items-center gap-2">
              <span>📁</span>
              导出文件
            </span>
            <span>{expandedSections.includes("exports") ? "▼" : "▶"}</span>
          </button>
          {expandedSections.includes("exports") && (
            <div className="ml-4 space-y-1">
              {exports.length === 0 ? (
                <p className="text-xs text-gray-400">暂无导出</p>
              ) : (
                exports.map((file) => (
                  <button
                    key={file.name}
                    onClick={() => handleExportClick(file)}
                    className="flex w-full items-center gap-2 rounded px-2 py-1 text-sm text-gray-600 hover:bg-gray-100"
                  >
                    <span>📄</span>
                    {file.name}
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
