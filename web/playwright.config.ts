import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // 测试目录
  testDir: './e2e',

  // 并行运行测试
  fullyParallel: true,

  // 失败时不重试（CI 中可以设置为 2）
  retries: process.env.CI ? 2 : 0,

  // 并行工作进程数
  workers: process.env.CI ? 1 : undefined,

  // 测试报告
  reporter: 'html',

  // 全局设置
  use: {
    // 基础 URL
    baseURL: 'http://localhost:3000',

    // 收集失败测试的 trace
    trace: 'on-first-retry',

    // 截图设置
    screenshot: 'only-on-failure',
  },

  // 配置不同浏览器的测试项目
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  // 在测试开始前启动开发服务器
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
