/**
 * 设计令牌 (Design Tokens)
 *
 * 基于 Ant Design 设计规范，定义统一的设计变量
 * 参考: https://ant.design/docs/spec/colors
 */

// 品牌色
export const colors = {
  // 主色 - 蓝色
  primary: "#2563eb",
  primaryHover: "#3b82f6",
  primaryActive: "#1d4ed8",
  primaryBg: "#eff6ff",
  primaryBgHover: "#dbeafe",
  primaryBorder: "#93c5fd",

  // 成功色 - 绿色
  success: "#52c41a",
  successHover: "#73d13d",
  successActive: "#389e0d",
  successBg: "#f6ffed",
  successBorder: "#b7eb8f",

  // 警告色 - 橙色
  warning: "#faad14",
  warningHover: "#ffc53d",
  warningActive: "#d48806",
  warningBg: "#fffbe6",
  warningBorder: "#ffe58f",

  // 错误色 - 红色
  error: "#ff4d4f",
  errorHover: "#ff7875",
  errorActive: "#d9363e",
  errorBg: "#fff2f0",
  errorBorder: "#ffccc7",

  // 信息色 - 蓝色
  info: "#1890ff",
  infoBg: "#e6f4ff",
  infoBorder: "#91caff",

  // 中性色
  text: "#1f2937",
  textSecondary: "#6b7280",
  textTertiary: "#9ca3af",
  textDisabled: "#d1d5db",

  // 边框
  border: "#e5e7eb",
  borderSecondary: "#f0f0f0",

  // 背景
  bgBase: "#ffffff",
  bgLayout: "#f5f7fa",
  bgContainer: "#ffffff",
  bgElevated: "#ffffff",
  bgSpotlight: "#fafafa",

  // 填充色
  fill: "#f3f4f6",
  fillSecondary: "#f9fafb",
  fillTertiary: "#fafafa",
};

// 深色模式色彩
export const darkColors = {
  // 主色
  primary: "#3b82f6",
  primaryHover: "#60a5fa",
  primaryActive: "#2563eb",
  primaryBg: "#172554",
  primaryBgHover: "#1e3a8a",
  primaryBorder: "#1d4ed8",

  // 成功色
  success: "#52c41a",
  successBg: "#162312",
  successBorder: "#274916",

  // 警告色
  warning: "#faad14",
  warningBg: "#2b2111",
  warningBorder: "#594214",

  // 错误色
  error: "#ff4d4f",
  errorBg: "#2c1618",
  errorBorder: "#58181c",

  // 信息色
  info: "#1890ff",
  infoBg: "#111a2c",
  infoBorder: "#153450",

  // 中性色
  text: "#f9fafb",
  textSecondary: "#9ca3af",
  textTertiary: "#6b7280",
  textDisabled: "#4b5563",

  // 边框
  border: "#374151",
  borderSecondary: "#1f2937",

  // 背景
  bgBase: "#111827",
  bgLayout: "#0f172a",
  bgContainer: "#1f2937",
  bgElevated: "#374151",
  bgSpotlight: "#1f2937",

  // 填充色
  fill: "#374151",
  fillSecondary: "#1f2937",
  fillTertiary: "#111827",
};

// 间距 - 基于 8px 基数
export const spacing = {
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

// 圆角
export const borderRadius = {
  xs: 2,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
};

// 字体大小
export const fontSize = {
  xs: 12,
  sm: 13,
  md: 14,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

// 行高
export const lineHeight = {
  tight: 1.25,
  normal: 1.5,
  relaxed: 1.75,
};

// 字重
export const fontWeight = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
};

// 阴影
export const shadows = {
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
  md: "0 2px 8px rgba(0, 0, 0, 0.08)",
  lg: "0 4px 16px rgba(0, 0, 0, 0.12)",
  xl: "0 8px 24px rgba(0, 0, 0, 0.15)",
  inner: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)",
  primary: "0 2px 8px rgba(37, 99, 235, 0.25)",
};

// 深色模式阴影
export const darkShadows = {
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.3)",
  md: "0 2px 8px rgba(0, 0, 0, 0.4)",
  lg: "0 4px 16px rgba(0, 0, 0, 0.5)",
  xl: "0 8px 24px rgba(0, 0, 0, 0.6)",
  inner: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.3)",
  primary: "0 2px 8px rgba(59, 130, 246, 0.4)",
};

// 过渡动画
export const transitions = {
  fast: "0.15s ease",
  normal: "0.25s ease",
  slow: "0.35s ease",
};

// Z-index 层级
export const zIndex = {
  dropdown: 1000,
  sticky: 1100,
  modal: 1200,
  popover: 1300,
  tooltip: 1400,
};

// Ant Design 主题配置
export const antdLightTheme = {
  token: {
    // 品牌色
    colorPrimary: colors.primary,
    colorSuccess: colors.success,
    colorWarning: colors.warning,
    colorError: colors.error,
    colorInfo: colors.info,

    // 文字颜色
    colorText: colors.text,
    colorTextSecondary: colors.textSecondary,
    colorTextTertiary: colors.textTertiary,
    colorTextDisabled: colors.textDisabled,

    // 背景色
    colorBgBase: colors.bgBase,
    colorBgLayout: colors.bgLayout,
    colorBgContainer: colors.bgContainer,
    colorBgElevated: colors.bgElevated,
    colorBgSpotlight: colors.bgSpotlight,

    // 边框
    colorBorder: colors.border,
    colorBorderSecondary: colors.borderSecondary,

    // 填充
    colorFill: colors.fill,
    colorFillSecondary: colors.fillSecondary,
    colorFillTertiary: colors.fillTertiary,

    // 圆角
    borderRadius: borderRadius.md,
    borderRadiusLG: borderRadius.lg,
    borderRadiusSM: borderRadius.sm,
    borderRadiusXS: borderRadius.xs,

    // 间距
    marginXS: spacing.xs,
    marginSM: spacing.sm,
    margin: spacing.md,
    marginLG: spacing.lg,
    marginXL: spacing.xl,
    marginXXL: spacing.xxl,

    paddingXS: spacing.xs,
    paddingSM: spacing.sm,
    padding: spacing.md,
    paddingLG: spacing.lg,
    paddingXL: spacing.xl,

    // 字体
    fontFamily:
      "var(--font-geist-sans), -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize: fontSize.md,
    fontSizeSM: fontSize.sm,
    fontSizeLG: fontSize.lg,
    fontSizeXL: fontSize.xl,

    // 行高
    lineHeight: lineHeight.normal,

    // 阴影
    boxShadow: shadows.md,
    boxShadowSecondary: shadows.lg,

    // 动效
    motionDurationFast: "0.1s",
    motionDurationMid: "0.2s",
    motionDurationSlow: "0.3s",
    motionEaseInOut: "cubic-bezier(0.645, 0.045, 0.355, 1)",
    motionEaseOut: "cubic-bezier(0.215, 0.61, 0.355, 1)",
    motionEaseIn: "cubic-bezier(0.55, 0.055, 0.675, 0.19)",
  },
  components: {
    Layout: {
      headerBg: colors.bgBase,
      headerHeight: 56,
      siderBg: colors.bgBase,
      bodyBg: colors.bgLayout,
      footerBg: colors.bgBase,
    },
    Card: {
      headerBg: "transparent",
      borderRadiusLG: borderRadius.lg,
    },
    Button: {
      borderRadius: borderRadius.md,
      primaryShadow: shadows.primary,
    },
    Menu: {
      itemBg: "transparent",
      itemHoverBg: colors.fillSecondary,
      itemSelectedBg: colors.primaryBg,
      itemSelectedColor: colors.primary,
      itemActiveBg: colors.primaryBgHover,
    },
    Input: {
      borderRadius: borderRadius.md,
    },
    Table: {
      headerBg: colors.fillTertiary,
      rowHoverBg: colors.fillSecondary,
      borderColor: colors.borderSecondary,
    },
    Timeline: {
      tailColor: colors.borderSecondary,
    },
    Tag: {
      borderRadiusSM: borderRadius.sm,
    },
    Modal: {
      borderRadiusLG: borderRadius.lg,
    },
    Message: {
      borderRadiusLG: borderRadius.md,
    },
  },
};

// 深色主题配置
export const antdDarkTheme = {
  token: {
    // 品牌色
    colorPrimary: darkColors.primary,
    colorSuccess: darkColors.success,
    colorWarning: darkColors.warning,
    colorError: darkColors.error,
    colorInfo: darkColors.info,

    // 文字颜色
    colorText: darkColors.text,
    colorTextSecondary: darkColors.textSecondary,
    colorTextTertiary: darkColors.textTertiary,
    colorTextDisabled: darkColors.textDisabled,

    // 背景色
    colorBgBase: darkColors.bgBase,
    colorBgLayout: darkColors.bgLayout,
    colorBgContainer: darkColors.bgContainer,
    colorBgElevated: darkColors.bgElevated,
    colorBgSpotlight: darkColors.bgSpotlight,

    // 边框
    colorBorder: darkColors.border,
    colorBorderSecondary: darkColors.borderSecondary,

    // 填充
    colorFill: darkColors.fill,
    colorFillSecondary: darkColors.fillSecondary,
    colorFillTertiary: darkColors.fillTertiary,

    // 其他配置继承浅色主题
    borderRadius: borderRadius.md,
    borderRadiusLG: borderRadius.lg,
    borderRadiusSM: borderRadius.sm,
    borderRadiusXS: borderRadius.xs,

    marginXS: spacing.xs,
    marginSM: spacing.sm,
    margin: spacing.md,
    marginLG: spacing.lg,
    marginXL: spacing.xl,
    marginXXL: spacing.xxl,

    paddingXS: spacing.xs,
    paddingSM: spacing.sm,
    padding: spacing.md,
    paddingLG: spacing.lg,
    paddingXL: spacing.xl,

    fontFamily:
      "var(--font-geist-sans), -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize: fontSize.md,
    fontSizeSM: fontSize.sm,
    fontSizeLG: fontSize.lg,
    fontSizeXL: fontSize.xl,

    lineHeight: lineHeight.normal,

    boxShadow: darkShadows.md,
    boxShadowSecondary: darkShadows.lg,

    motionDurationFast: "0.1s",
    motionDurationMid: "0.2s",
    motionDurationSlow: "0.3s",
    motionEaseInOut: "cubic-bezier(0.645, 0.045, 0.355, 1)",
    motionEaseOut: "cubic-bezier(0.215, 0.61, 0.355, 1)",
    motionEaseIn: "cubic-bezier(0.55, 0.055, 0.675, 0.19)",
  },
  components: {
    Layout: {
      headerBg: darkColors.bgContainer,
      headerHeight: 56,
      siderBg: darkColors.bgContainer,
      bodyBg: darkColors.bgLayout,
      footerBg: darkColors.bgContainer,
    },
    Card: {
      headerBg: "transparent",
      borderRadiusLG: borderRadius.lg,
      colorBgContainer: darkColors.bgContainer,
    },
    Button: {
      borderRadius: borderRadius.md,
      primaryShadow: darkShadows.primary,
    },
    Menu: {
      itemBg: "transparent",
      darkItemBg: "transparent",
      darkItemHoverBg: darkColors.fillSecondary,
      darkItemSelectedBg: darkColors.primaryBg,
      darkItemSelectedColor: darkColors.primary,
    },
    Input: {
      borderRadius: borderRadius.md,
      colorBgContainer: darkColors.bgContainer,
    },
    Table: {
      headerBg: darkColors.fillTertiary,
      rowHoverBg: darkColors.fillSecondary,
      borderColor: darkColors.borderSecondary,
    },
    Timeline: {
      tailColor: darkColors.borderSecondary,
    },
    Tag: {
      borderRadiusSM: borderRadius.sm,
    },
    Modal: {
      borderRadiusLG: borderRadius.lg,
      contentBg: darkColors.bgContainer,
      headerBg: darkColors.bgContainer,
    },
    Message: {
      borderRadiusLG: borderRadius.md,
      contentBg: darkColors.bgContainer,
    },
  },
};
