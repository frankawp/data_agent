/**
 * ChatSidebar 组件测试
 * 覆盖测试用例: TC-C-001 ~ TC-C-012
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatSidebar } from '@/components/chat/ChatSidebar';

describe('ChatSidebar 组件测试', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * TC-C-001: 初始欢迎消息
   */
  describe('TC-C-001: 初始欢迎消息', () => {
    it('应该显示初始欢迎消息', () => {
      render(<ChatSidebar />);

      expect(
        screen.getByText('我可以帮助您进行数据查询、分析和可视化。请描述您的需求。')
      ).toBeInTheDocument();
    });

    it('应该显示 "数据分析助手" 标题', () => {
      render(<ChatSidebar />);

      expect(screen.getByText('数据分析助手')).toBeInTheDocument();
    });
  });

  /**
   * TC-C-002: 发送消息 - Enter 键
   */
  describe('TC-C-002: 发送消息 - Enter 键', () => {
    it('按 Enter 应该发送消息', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: { content: '收到' } }),
      });

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '测试消息');
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

      await waitFor(() => {
        expect(screen.getByText('测试消息')).toBeInTheDocument();
      });
    });

    it('发送后输入框应该清空', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: { content: '收到' } }),
      });

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText(
        '描述您的数据分析需求...'
      ) as HTMLTextAreaElement;
      await userEvent.type(textarea, '测试消息');
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

      await waitFor(() => {
        expect(textarea.value).toBe('');
      });
    });
  });

  /**
   * TC-C-003: 换行 - Shift+Enter
   */
  describe('TC-C-003: 换行 - Shift+Enter', () => {
    it('Shift+Enter 不应该发送消息', async () => {
      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '第一行');
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: true });

      // fetch 不应该被调用
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  /**
   * TC-C-004: 发送消息 - 点击按钮
   */
  describe('TC-C-004: 发送消息 - 点击按钮', () => {
    it('点击发送按钮应该发送消息', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: { content: '收到' } }),
      });

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '测试消息');

      const sendButton = screen.getByText('发送');
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('测试消息')).toBeInTheDocument();
      });
    });
  });

  /**
   * TC-C-005: 空消息不可发送
   */
  describe('TC-C-005: 空消息不可发送', () => {
    it('输入框为空时发送按钮应该禁用', () => {
      render(<ChatSidebar />);

      const sendButton = screen.getByText('发送');
      expect(sendButton).toBeDisabled();
    });

    it('只有空格时发送按钮应该禁用', async () => {
      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '   ');

      const sendButton = screen.getByText('发送');
      expect(sendButton).toBeDisabled();
    });

    it('空输入按 Enter 不应发送', async () => {
      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  /**
   * TC-C-006: 加载动画显示
   */
  describe('TC-C-006: 加载动画显示', () => {
    it('发送消息后应该显示加载状态', async () => {
      // 永不解析的 Promise，保持加载状态
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      );

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '测试');
      fireEvent.click(screen.getByText('发送'));

      // 发送按钮应该显示 "..."
      await waitFor(() => {
        expect(screen.getByText('...')).toBeInTheDocument();
      });
    });

    it('加载中输入框应该禁用', async () => {
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      );

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText(
        '描述您的数据分析需求...'
      ) as HTMLTextAreaElement;
      await userEvent.type(textarea, '测试');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        expect(textarea).toBeDisabled();
      });
    });

    it('应该显示三个跳动圆点动画', async () => {
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      );

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '测试');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        const dots = document.querySelectorAll('.animate-bounce');
        expect(dots.length).toBe(3);
      });
    });
  });

  /**
   * TC-C-007: 助手响应显示
   */
  describe('TC-C-007: 助手响应显示', () => {
    it('应该显示助手响应内容', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: { content: '这是助手的回复' } }),
      });

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '你好');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        expect(screen.getByText('这是助手的回复')).toBeInTheDocument();
      });
    });

    it('响应后输入框应该恢复可用', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: { content: '回复' } }),
      });

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText(
        '描述您的数据分析需求...'
      ) as HTMLTextAreaElement;
      await userEvent.type(textarea, '测试');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        expect(textarea).not.toBeDisabled();
      });
    });
  });

  /**
   * TC-C-008: 清空对话
   */
  describe('TC-C-008: 清空对话', () => {
    it('点击清空按钮应该重置对话', async () => {
      // 先发送一条消息
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ message: { content: '回复' } }),
        })
        .mockResolvedValueOnce({}); // reset API

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '测试消息');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        expect(screen.getByText('测试消息')).toBeInTheDocument();
      });

      // 点击清空
      fireEvent.click(screen.getByText('清空'));

      await waitFor(() => {
        // 应该只剩下初始欢迎消息
        expect(
          screen.getByText('我可以帮助您进行数据查询、分析和可视化。请描述您的需求。')
        ).toBeInTheDocument();
        expect(screen.queryByText('测试消息')).not.toBeInTheDocument();
      });
    });

    it('清空应该调用 reset API', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({});

      render(<ChatSidebar />);
      fireEvent.click(screen.getByText('清空'));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/chat/reset', {
          method: 'POST',
        });
      });
    });
  });

  /**
   * TC-C-010: 发送失败错误处理
   */
  describe('TC-C-010: 发送失败错误处理', () => {
    it('API 失败时应该显示错误消息', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('网络错误'));

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '测试');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        expect(screen.getByText(/发送失败/)).toBeInTheDocument();
      });
    });

    it('HTTP 错误时应该显示错误消息', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: '服务器错误' }),
      });

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '测试');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        expect(screen.getByText(/发送失败/)).toBeInTheDocument();
      });
    });

    it('错误后输入框应该恢复可用', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('错误'));

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText(
        '描述您的数据分析需求...'
      ) as HTMLTextAreaElement;
      await userEvent.type(textarea, '测试');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        expect(textarea).not.toBeDisabled();
      });
    });
  });

  /**
   * TC-C-011: 用户消息样式
   */
  describe('TC-C-011: 用户消息样式', () => {
    it('用户消息应该有蓝色背景', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: { content: '回复' } }),
      });

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '用户消息');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        const userMessage = screen.getByText('用户消息');
        expect(userMessage.closest('div')).toHaveClass('bg-blue-600');
      });
    });

    it('用户消息应该右对齐', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: { content: '回复' } }),
      });

      render(<ChatSidebar />);

      const textarea = screen.getByPlaceholderText('描述您的数据分析需求...');
      await userEvent.type(textarea, '用户消息');
      fireEvent.click(screen.getByText('发送'));

      await waitFor(() => {
        const userMessage = screen.getByText('用户消息');
        const container = userMessage.closest('div')?.parentElement;
        expect(container).toHaveClass('justify-end');
      });
    });
  });

  /**
   * TC-C-012: 助手消息样式
   */
  describe('TC-C-012: 助手消息样式', () => {
    it('助手消息应该有灰色背景', () => {
      render(<ChatSidebar />);

      const assistantMessage = screen.getByText(
        '我可以帮助您进行数据查询、分析和可视化。请描述您的需求。'
      );
      expect(assistantMessage.closest('div')).toHaveClass('bg-gray-100');
    });

    it('助手消息应该左对齐', () => {
      render(<ChatSidebar />);

      const assistantMessage = screen.getByText(
        '我可以帮助您进行数据查询、分析和可视化。请描述您的需求。'
      );
      const container = assistantMessage.closest('div')?.parentElement;
      expect(container).toHaveClass('justify-start');
    });
  });
});
