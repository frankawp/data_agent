"use client";

/**
 * 主题 Provider
 *
 * 支持深色/浅色模式切换，并持久化到 localStorage
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { ConfigProvider, theme as antdTheme } from "antd";
import zhCN from "antd/locale/zh_CN";
import { antdLightTheme, antdDarkTheme } from "@/styles/tokens";

type ThemeMode = "light" | "dark" | "system";

interface ThemeContextType {
  mode: ThemeMode;
  isDark: boolean;
  setMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_KEY = "data-agent-theme";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>("system");
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  // 获取系统主题偏好
  const getSystemTheme = useCallback(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }, []);

  // 计算当前是否为深色模式
  const computeIsDark = useCallback(
    (themeMode: ThemeMode) => {
      if (themeMode === "system") {
        return getSystemTheme();
      }
      return themeMode === "dark";
    },
    [getSystemTheme]
  );

  // 初始化主题
  useEffect(() => {
    const saved = localStorage.getItem(THEME_KEY) as ThemeMode | null;
    const initialMode = saved || "system";
    setModeState(initialMode);
    setIsDark(computeIsDark(initialMode));
    setMounted(true);
  }, [computeIsDark]);

  // 监听系统主题变化
  useEffect(() => {
    if (mode !== "system") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (e: MediaQueryListEvent) => {
      setIsDark(e.matches);
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [mode]);

  // 更新 document class
  useEffect(() => {
    if (!mounted) return;
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark, mounted]);

  const setMode = useCallback(
    (newMode: ThemeMode) => {
      setModeState(newMode);
      setIsDark(computeIsDark(newMode));
      localStorage.setItem(THEME_KEY, newMode);
    },
    [computeIsDark]
  );

  const toggleTheme = useCallback(() => {
    const newMode = isDark ? "light" : "dark";
    setMode(newMode);
  }, [isDark, setMode]);

  // 合并主题配置
  const themeConfig = isDark
    ? {
        ...antdDarkTheme,
        algorithm: antdTheme.darkAlgorithm,
      }
    : antdLightTheme;

  // 默认值用于服务端渲染
  const defaultContextValue: ThemeContextType = {
    mode: "system",
    isDark: false,
    setMode: () => {},
    toggleTheme: () => {},
  };

  // 避免服务端渲染闪烁，但仍需提供 context
  if (!mounted) {
    return (
      <ThemeContext.Provider value={defaultContextValue}>
        <ConfigProvider locale={zhCN} theme={antdLightTheme}>
          {children}
        </ConfigProvider>
      </ThemeContext.Provider>
    );
  }

  return (
    <ThemeContext.Provider value={{ mode, isDark, setMode, toggleTheme }}>
      <ConfigProvider locale={zhCN} theme={themeConfig}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
