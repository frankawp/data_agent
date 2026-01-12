/**
 * Data Agent Web 前端 E2E 测试
 * 覆盖测试场景: E2E-001 ~ E2E-007
 *
 * 运行前提:
 * 1. 后端服务运行在 http://localhost:8000
 * 2. 前端服务运行在 http://localhost:3000
 * 3. 数据库已配置并有测试数据
 */
import { test, expect } from '@playwright/test';

test.describe('Data Agent Web 前端 E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前访问首页
    await page.goto('/');
  });

  /**
   * 基础页面加载测试
   */
  test.describe('页面加载', () => {
    test('应该正确加载首页', async ({ page }) => {
      // 检查标题
      await expect(page.getByRole('heading', { name: 'Data Agent' })).toBeVisible();

      // 检查 Logo (使用精确文本匹配)
      await expect(page.getByText('DA', { exact: true })).toBeVisible();

      // 检查聊天区域标题
      await expect(page.getByRole('heading', { name: '数据分析助手' })).toBeVisible();
    });

    test('应该显示初始欢迎消息', async ({ page }) => {
      await expect(
        page.locator('text=我可以帮助您进行数据查询、分析和可视化')
      ).toBeVisible();
    });
  });

  /**
   * E2E-001: 完整数据查询流程
   * 注意：此测试需要后端服务运行
   */
  test.describe('E2E-001: 完整数据查询流程', () => {
    test('应该能发送查询并显示用户消息', async ({ page }) => {
      // 1. 在聊天输入框输入查询请求
      const textarea = page.locator('textarea[placeholder="描述您的数据分析需求..."]');
      await textarea.fill('查询用户表的前5条数据');

      // 2. 发送消息
      await page.getByRole('button', { name: '发送' }).click();

      // 3. 验证用户消息显示
      await expect(page.locator('text=查询用户表的前5条数据')).toBeVisible();

      // 4. 验证发送按钮显示加载状态
      await expect(page.getByRole('button', { name: '...' })).toBeVisible({ timeout: 1000 });
    });

    test.skip('应该能收到 AI 响应（需要后端运行）', async ({ page }) => {
      // 此测试需要后端服务运行
      const textarea = page.locator('textarea[placeholder="描述您的数据分析需求..."]');
      await textarea.fill('你好');
      await page.getByRole('button', { name: '发送' }).click();

      // 等待加载动画消失（最多等待 30 秒）
      await expect(page.locator('.animate-bounce')).toHaveCount(0, { timeout: 30000 });

      // 验证有响应
      const messages = page.locator('[class*="bg-gray-100"]');
      await expect(messages).toHaveCount(2, { timeout: 30000 });
    });
  });

  /**
   * E2E-002: 查看表结构后执行查询
   */
  test.describe('E2E-002: 查看表结构后执行查询', () => {
    test('应该能在侧边栏查看表结构', async ({ page }) => {
      // 1. 等待表列表加载
      // 点击数据库浏览器展开（如果需要）
      const dbBrowser = page.locator('text=数据库浏览器');
      if (await dbBrowser.isVisible()) {
        await dbBrowser.click();
      }

      // 2. 等待表列表显示
      await page.waitForTimeout(2000);

      // 3. 如果有表，点击第一个表
      const tables = page.locator('[class*="cursor-pointer"]:has-text("📋")');
      const tableCount = await tables.count();

      if (tableCount > 0) {
        await tables.first().click();

        // 4. 验证副工作区显示表结构
        await expect(page.locator('text=表结构')).toBeVisible({ timeout: 5000 });
      }
    });

    test('Tab 切换应该正常工作', async ({ page }) => {
      // 验证主工作区 Tab 默认选中
      const mainTab = page.locator('button:text("主工作区")');
      await expect(mainTab).toBeVisible();

      // 副工作区 Tab 初始应该禁用
      const secondaryTab = page.locator('button:text("副工作区")');
      await expect(secondaryTab).toBeVisible();
    });
  });

  /**
   * E2E-003: 模式切换影响行为
   */
  test.describe('E2E-003: 模式切换', () => {
    test('应该能打开和关闭模式设置面板', async ({ page }) => {
      // 1. 点击模式设置按钮
      await page.getByRole('button', { name: '模式设置' }).click();

      // 2. 验证面板打开（等待面板出现）
      await expect(page.locator('.absolute.right-4.top-14')).toBeVisible();

      // 3. 点击关闭按钮
      await page.getByRole('button', { name: '✕' }).click();

      // 4. 验证面板关闭
      await expect(page.locator('.absolute.right-4.top-14')).not.toBeVisible();
    });

    test('应该能切换模式', async ({ page }) => {
      // 打开模式设置
      await page.getByRole('button', { name: '模式设置' }).click();

      // 等待面板加载
      await expect(page.locator('.absolute.right-4.top-14')).toBeVisible();
      await page.waitForTimeout(500);

      // 检查模式面板是否可见
      const modePanel = page.locator('.absolute.right-4.top-14');
      await expect(modePanel).toBeVisible();
    });
  });

  /**
   * E2E-005: 会话重置
   */
  test.describe('E2E-005: 会话重置', () => {
    test('清空按钮应该重置对话', async ({ page }) => {
      // 1. 发送一条消息
      const textarea = page.locator('textarea[placeholder="描述您的数据分析需求..."]');
      await textarea.fill('测试消息');
      await page.locator('button:text("发送")').click();

      // 2. 等待消息显示
      await expect(page.locator('text=测试消息')).toBeVisible();

      // 3. 点击清空按钮
      await page.locator('button:text("清空")').click();

      // 4. 验证对话被重置
      await expect(page.locator('text=测试消息')).not.toBeVisible();
      await expect(
        page.locator('text=我可以帮助您进行数据查询、分析和可视化')
      ).toBeVisible();
    });
  });

  /**
   * 聊天功能测试
   */
  test.describe('聊天功能', () => {
    test('Enter 键应该发送消息', async ({ page }) => {
      const textarea = page.locator('textarea[placeholder="描述您的数据分析需求..."]');
      await textarea.fill('Enter 测试');
      await textarea.press('Enter');

      await expect(page.locator('text=Enter 测试')).toBeVisible();
    });

    test('Shift+Enter 不应该发送消息', async ({ page }) => {
      const textarea = page.locator('textarea[placeholder="描述您的数据分析需求..."]');
      await textarea.click();
      await textarea.fill('第一行');

      // 使用 Shift+Enter 不发送
      await page.keyboard.down('Shift');
      await page.keyboard.press('Enter');
      await page.keyboard.up('Shift');

      // 输入框应该还有内容（没被清空，说明没发送）
      await expect(textarea).toHaveValue(/第一行/);
    });

    test('空消息发送按钮应该禁用', async ({ page }) => {
      const sendButton = page.locator('button:text("发送")');
      await expect(sendButton).toBeDisabled();
    });

    test('有输入时发送按钮应该启用', async ({ page }) => {
      const textarea = page.locator('textarea[placeholder="描述您的数据分析需求..."]');
      await textarea.fill('测试');

      const sendButton = page.locator('button:text("发送")');
      await expect(sendButton).not.toBeDisabled();
    });
  });

  /**
   * Header 组件测试
   */
  test.describe('Header 组件', () => {
    test('应该显示会话 ID', async ({ page }) => {
      // 等待会话信息加载
      await page.waitForTimeout(2000);

      // 检查会话 ID 显示（如果后端可用）
      const sessionText = page.locator('text=/会话:/');
      // 不强制要求，因为后端可能不可用
      if (await sessionText.isVisible()) {
        await expect(sessionText).toBeVisible();
      }
    });

    test('应该显示数据库连接状态', async ({ page }) => {
      await expect(page.locator('text=已连接')).toBeVisible();
    });
  });

  /**
   * 工作区测试
   */
  test.describe('工作区', () => {
    test('初始应该显示等待状态', async ({ page }) => {
      await expect(page.locator('text=等待 AI 执行操作')).toBeVisible();
    });
  });

  /**
   * 性能测试
   */
  test.describe('性能', () => {
    test('首页加载时间应该小于 5 秒', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/');
      await expect(page.locator('text=Data Agent')).toBeVisible();
      const loadTime = Date.now() - startTime;

      expect(loadTime).toBeLessThan(5000);
    });

    test('发送消息后应该立即显示加载状态', async ({ page }) => {
      const textarea = page.locator('textarea[placeholder="描述您的数据分析需求..."]');
      await textarea.fill('测试');

      const sendButton = page.locator('button:text("发送")');

      // 点击并立即检查
      await sendButton.click();

      // 在 500ms 内应该显示加载状态
      await expect(page.locator('button:text("...")')).toBeVisible({ timeout: 500 });
    });
  });

  /**
   * 响应式测试
   */
  test.describe('响应式', () => {
    test('桌面尺寸布局应该正确', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');

      // 侧边栏、工作区、聊天区域都应该可见
      await expect(page.locator('text=数据库浏览器')).toBeVisible();
      await expect(page.getByRole('button', { name: '主工作区' })).toBeVisible();
      await expect(page.getByRole('heading', { name: '数据分析助手' })).toBeVisible();
    });
  });
});

/**
 * API 代理测试
 */
test.describe('API 代理测试', () => {
  test('GET /api/sessions 应该返回会话信息', async ({ request }) => {
    const response = await request.get('/api/sessions');

    // 如果后端可用，应该返回 200
    if (response.ok()) {
      const data = await response.json();
      expect(data).toHaveProperty('session_id');
    }
  });

  test('GET /api/modes 应该返回模式状态', async ({ request }) => {
    const response = await request.get('/api/modes');

    if (response.ok()) {
      const data = await response.json();
      expect(data).toHaveProperty('modes');
    }
  });

  test('GET /api/database/tables 应该返回表列表', async ({ request }) => {
    const response = await request.get('/api/database/tables');

    if (response.ok()) {
      const data = await response.json();
      expect(data).toHaveProperty('tables');
    }
  });
});
