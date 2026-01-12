"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";

// 副工作区内容类型
export interface SecondaryContent {
  type: "table" | "model" | "export" | "graph" | "step";
  data: Record<string, unknown>;
}

// 历史步骤信息
export interface HistoricalStep {
  index: number;
  toolName: string;
  args: Record<string, unknown>;
  result: string;
}

// 当前工具执行结果
export interface ToolResult {
  toolName: string;
  args: Record<string, unknown>;
  result: string;
}

// 流式执行步骤
export interface StreamingStep {
  step: number;
  toolName: string;
  args: Record<string, unknown>;
  result?: string;
  status: "running" | "completed" | "error";
}

// 工作区上下文类型
interface WorkspaceContextType {
  // Tab 状态
  activeTab: "main" | "secondary";
  setActiveTab: (tab: "main" | "secondary") => void;

  // 副工作区内容
  secondaryContent: SecondaryContent | null;
  setSecondaryContent: (content: SecondaryContent | null) => void;

  // 历史查看模式
  viewMode: "live" | "historical";
  historicalStep: HistoricalStep | null;
  showHistoricalStep: (step: HistoricalStep) => void;
  exitHistoricalView: () => void;

  // 当前工具执行结果
  currentToolResult: ToolResult | null;
  setCurrentToolResult: (result: ToolResult | null) => void;

  // 执行历史
  stepHistory: HistoricalStep[];
  addStepToHistory: (step: HistoricalStep) => void;
  clearHistory: () => void;

  // 流式执行状态
  isStreaming: boolean;
  streamingSteps: StreamingStep[];
  startStreaming: () => void;
  addStreamingStep: (step: Omit<StreamingStep, "status">) => void;
  updateStreamingStepResult: (stepNum: number, result: string) => void;
  finishStreaming: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  // Tab 状态
  const [activeTab, setActiveTab] = useState<"main" | "secondary">("main");

  // 副工作区内容
  const [secondaryContent, setSecondaryContent] =
    useState<SecondaryContent | null>(null);

  // 历史查看模式
  const [viewMode, setViewMode] = useState<"live" | "historical">("live");
  const [historicalStep, setHistoricalStep] = useState<HistoricalStep | null>(
    null
  );

  // 当前工具执行结果
  const [currentToolResult, setCurrentToolResult] = useState<ToolResult | null>(
    null
  );

  // 执行历史
  const [stepHistory, setStepHistory] = useState<HistoricalStep[]>([]);

  // 流式执行状态
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingSteps, setStreamingSteps] = useState<StreamingStep[]>([]);

  // 查看历史步骤
  const showHistoricalStep = useCallback((step: HistoricalStep) => {
    setHistoricalStep(step);
    setViewMode("historical");
    setActiveTab("main");
  }, []);

  // 退出历史查看
  const exitHistoricalView = useCallback(() => {
    setHistoricalStep(null);
    setViewMode("live");
  }, []);

  // 添加步骤到历史
  const addStepToHistory = useCallback((step: HistoricalStep) => {
    setStepHistory((prev) => [...prev, step]);
  }, []);

  // 清除历史
  const clearHistory = useCallback(() => {
    setStepHistory([]);
  }, []);

  // 开始流式执行
  const startStreaming = useCallback(() => {
    setIsStreaming(true);
    setStreamingSteps([]);
    setActiveTab("main");
  }, []);

  // 添加流式步骤
  const addStreamingStep = useCallback((step: Omit<StreamingStep, "status">) => {
    setStreamingSteps((prev) => [...prev, { ...step, status: "running" }]);
  }, []);

  // 更新流式步骤结果
  const updateStreamingStepResult = useCallback((stepNum: number, result: string) => {
    setStreamingSteps((prev) =>
      prev.map((s) =>
        s.step === stepNum ? { ...s, result, status: "completed" } : s
      )
    );
  }, []);

  // 结束流式执行
  const finishStreaming = useCallback(() => {
    setIsStreaming(false);
    // 将流式步骤转换为历史步骤
    setStreamingSteps((prev) => {
      prev.forEach((step, index) => {
        if (step.result) {
          addStepToHistory({
            index: Date.now() + index,
            toolName: step.toolName,
            args: step.args,
            result: step.result,
          });
        }
      });
      return prev;
    });
  }, [addStepToHistory]);

  return (
    <WorkspaceContext.Provider
      value={{
        activeTab,
        setActiveTab,
        secondaryContent,
        setSecondaryContent,
        viewMode,
        historicalStep,
        showHistoricalStep,
        exitHistoricalView,
        currentToolResult,
        setCurrentToolResult,
        stepHistory,
        addStepToHistory,
        clearHistory,
        isStreaming,
        streamingSteps,
        startStreaming,
        addStreamingStep,
        updateStreamingStepResult,
        finishStreaming,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
