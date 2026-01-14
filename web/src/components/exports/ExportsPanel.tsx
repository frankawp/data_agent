"use client";

/**
 * 导出文件面板
 *
 * 显示当前会话的所有导出文件，支持预览和下载。
 */

import { useState, useEffect, useCallback } from "react";

// 文件类型
interface ExportFile {
  name: string;
  path: string;
  size: number;
  modified: number;
  type: string;
}

// 预览内容
interface PreviewContent {
  content: string;
  type: "text" | "code" | "table" | "image";
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// 格式化时间
function formatTime(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// 获取文件图标
function getFileIcon(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const icons: Record<string, string> = {
    csv: "📊",
    xlsx: "📊",
    xls: "📊",
    png: "🖼️",
    jpg: "🖼️",
    jpeg: "🖼️",
    gif: "🖼️",
    svg: "🖼️",
    json: "📄",
    sql: "🗃️",
    py: "🐍",
    txt: "📝",
    md: "📝",
    html: "🌐",
    pdf: "📕",
    pkl: "🤖",
    joblib: "🤖",
    model: "🤖",
  };
  return icons[ext] || "📁";
}

// 获取文件类型标签
function getFileTypeLabel(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const labels: Record<string, string> = {
    csv: "数据表",
    xlsx: "Excel",
    png: "图片",
    jpg: "图片",
    json: "JSON",
    sql: "SQL",
    py: "Python",
    pkl: "模型",
    joblib: "模型",
  };
  return labels[ext] || ext.toUpperCase();
}

export function ExportsPanel() {
  const [files, setFiles] = useState<ExportFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<ExportFile | null>(null);
  const [preview, setPreview] = useState<PreviewContent | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // 获取导出文件列表
  const fetchExports = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/sessions/exports");
      if (!res.ok) {
        throw new Error("获取导出文件失败");
      }
      const data = await res.json();
      setFiles(data.files || []);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExports();
    // 每 10 秒刷新一次
    const interval = setInterval(fetchExports, 10000);
    return () => clearInterval(interval);
  }, [fetchExports]);

  // 预览文件
  const handlePreview = async (file: ExportFile) => {
    setSelectedFile(file);
    setPreviewLoading(true);
    setPreview(null);

    try {
      const res = await fetch(`/api/sessions/exports/${file.name}/preview`);
      if (!res.ok) {
        throw new Error("预览失败");
      }
      const data = await res.json();
      setPreview(data);
    } catch (err) {
      setPreview({ content: `预览失败: ${(err as Error).message}`, type: "text" });
    } finally {
      setPreviewLoading(false);
    }
  };

  // 下载文件
  const handleDownload = (file: ExportFile) => {
    window.open(`/api/sessions/exports/${file.name}/download`, "_blank");
  };

  // 刷新列表
  const handleRefresh = () => {
    fetchExports();
  };

  return (
    <div className="flex h-full flex-col bg-white">
      {/* 头部 */}
      <div className="flex items-center justify-between border-b p-3">
        <div>
          <h3 className="flex items-center gap-2 font-semibold text-gray-800">
            <span>📦</span>
            <span>导出文件</span>
          </h3>
          <p className="text-xs text-gray-500">
            {loading ? "加载中..." : `${files.length} 个文件`}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="rounded p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 disabled:opacity-50"
          title="刷新"
        >
          <svg
            className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </button>
      </div>

      {/* 文件列表 */}
      <div className="flex-1 overflow-auto">
        {error ? (
          <div className="p-4 text-center text-red-500">
            <p>{error}</p>
            <button
              onClick={handleRefresh}
              className="mt-2 text-sm text-blue-500 hover:underline"
            >
              重试
            </button>
          </div>
        ) : files.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center p-4 text-gray-400">
            <span className="text-4xl">📭</span>
            <p className="mt-2 text-sm">暂无导出文件</p>
            <p className="text-xs">执行数据分析任务后会自动生成</p>
          </div>
        ) : (
          <div className="divide-y">
            {files.map((file) => (
              <div
                key={file.name}
                className={`cursor-pointer p-3 transition-colors hover:bg-gray-50 ${
                  selectedFile?.name === file.name ? "bg-blue-50" : ""
                }`}
                onClick={() => handlePreview(file)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{getFileIcon(file.name)}</span>
                  <div className="flex-1 overflow-hidden">
                    <p className="truncate text-sm font-medium text-gray-700">
                      {file.name}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <span className="rounded bg-gray-100 px-1.5 py-0.5">
                        {getFileTypeLabel(file.name)}
                      </span>
                      <span>{formatSize(file.size)}</span>
                      <span>•</span>
                      <span>{formatTime(file.modified)}</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(file);
                    }}
                    className="rounded p-1.5 text-gray-400 transition-colors hover:bg-gray-200 hover:text-gray-600"
                    title="下载"
                  >
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 预览区域 */}
      {selectedFile && (
        <div className="border-t">
          <div className="flex items-center justify-between bg-gray-50 px-3 py-2">
            <span className="text-sm font-medium text-gray-600">
              预览: {selectedFile.name}
            </span>
            <button
              onClick={() => {
                setSelectedFile(null);
                setPreview(null);
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div className="max-h-48 overflow-auto bg-gray-100 p-3">
            {previewLoading ? (
              <div className="flex items-center justify-center py-4 text-gray-400">
                <svg
                  className="mr-2 h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                加载中...
              </div>
            ) : preview ? (
              preview.type === "image" ? (
                <img
                  src={preview.content}
                  alt={selectedFile.name}
                  className="max-w-full"
                />
              ) : (
                <pre className="whitespace-pre-wrap break-all text-xs text-gray-700">
                  {preview.content}
                </pre>
              )
            ) : null}
          </div>
          <div className="flex gap-2 p-3">
            <button
              onClick={() => handleDownload(selectedFile)}
              className="flex-1 rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-600"
            >
              ⬇️ 下载文件
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExportsPanel;
