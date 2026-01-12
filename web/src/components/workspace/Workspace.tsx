"use client";

import { useWorkspace } from "@/hooks/useWorkspaceContext";
import { MainWorkspace } from "./MainWorkspace";
import { SecondaryWorkspace } from "./SecondaryWorkspace";

export function Workspace() {
  const { activeTab, setActiveTab, secondaryContent } = useWorkspace();

  return (
    <div className="flex h-full flex-col">
      {/* Tab 切换 */}
      <div className="flex border-b bg-white">
        <button
          onClick={() => setActiveTab("main")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "main"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          主工作区
        </button>
        <button
          onClick={() => setActiveTab("secondary")}
          disabled={!secondaryContent}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "secondary"
              ? "border-blue-600 text-blue-600"
              : secondaryContent
              ? "border-transparent text-gray-500 hover:text-gray-700"
              : "border-transparent text-gray-300 cursor-not-allowed"
          }`}
        >
          副工作区
          {secondaryContent && (
            <span className="text-xs text-gray-400">
              ({secondaryContent.type})
            </span>
          )}
        </button>
      </div>

      {/* 工作区内容 */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "main" ? (
          <MainWorkspace />
        ) : (
          <SecondaryWorkspace content={secondaryContent} />
        )}
      </div>
    </div>
  );
}
