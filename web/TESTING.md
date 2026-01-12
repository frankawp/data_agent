# 前端测试指南

本文档介绍如何运行 Data Agent Web 前端的测试。

## 测试框架

- **单元测试**: Jest + React Testing Library
- **E2E 测试**: Playwright

## 安装依赖

首次运行测试前，需要安装测试依赖：

```bash
cd web

# 如果遇到 npm 缓存权限问题，先运行：
sudo chown -R $(whoami) ~/.npm

# 安装依赖
npm install

# 安装 Playwright 浏览器
npx playwright install
```

## 运行测试

### 单元测试

```bash
# 运行所有单元测试
npm test

# 监听模式（开发时使用）
npm run test:watch

# 生成覆盖率报告
npm run test:coverage
```

### E2E 测试

E2E 测试需要前后端服务运行：

```bash
# 终端 1: 启动后端
cd /path/to/data_agent
python -m data_agent.api.main

# 终端 2: 启动前端
cd web
npm run dev

# 终端 3: 运行 E2E 测试
npm run test:e2e

# 使用 UI 模式（可视化调试）
npm run test:e2e:ui

# 有头模式（显示浏览器）
npm run test:e2e:headed
```

## 测试文件结构

```
web/
├── src/
│   └── __tests__/
│       └── components/
│           ├── Header.test.tsx      # Header 组件测试
│           ├── ChatSidebar.test.tsx # 聊天组件测试
│           ├── DataTable.test.tsx   # 数据表格测试
│           └── CodeViewer.test.tsx  # 代码查看器测试
├── e2e/
│   └── app.spec.ts                  # E2E 测试
├── jest.config.js                   # Jest 配置
├── jest.setup.js                    # Jest 设置
└── playwright.config.ts             # Playwright 配置
```

## 测试用例覆盖

### 单元测试覆盖

| 组件 | 测试文件 | 用例数 |
|------|---------|--------|
| Header | Header.test.tsx | 7 |
| ChatSidebar | ChatSidebar.test.tsx | 12 |
| DataTable | DataTable.test.tsx | 8 |
| CodeViewer | CodeViewer.test.tsx | 7 |

### E2E 测试覆盖

| 场景 | 描述 |
|------|------|
| 页面加载 | 首页加载、欢迎消息 |
| 聊天功能 | 发送消息、清空对话 |
| 模式设置 | 打开/关闭面板、切换模式 |
| 工作区 | Tab 切换、表结构查看 |
| API 测试 | sessions、modes、database |

## 编写新测试

### 单元测试示例

```tsx
import { render, screen } from '@testing-library/react';
import { MyComponent } from '@/components/MyComponent';

describe('MyComponent', () => {
  it('应该正确渲染', () => {
    render(<MyComponent />);
    expect(screen.getByText('预期文本')).toBeInTheDocument();
  });
});
```

### E2E 测试示例

```ts
import { test, expect } from '@playwright/test';

test('应该能完成某个流程', async ({ page }) => {
  await page.goto('/');
  await page.locator('button').click();
  await expect(page.locator('text=结果')).toBeVisible();
});
```

## 调试技巧

### Jest 调试

```bash
# 只运行特定测试文件
npm test -- Header.test.tsx

# 只运行匹配的测试
npm test -- -t "会话 ID"
```

### Playwright 调试

```bash
# 使用 UI 模式调试
npm run test:e2e:ui

# 生成 trace 文件
npx playwright test --trace on

# 查看测试报告
npx playwright show-report
```

## CI/CD 集成

GitHub Actions 配置示例：

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: cd web && npm ci

      - name: Run unit tests
        run: cd web && npm test

      - name: Install Playwright browsers
        run: cd web && npx playwright install --with-deps

      - name: Run E2E tests
        run: cd web && npm run test:e2e
```
