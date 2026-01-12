/**
 * Header 组件测试
 * 覆盖测试用例: TC-H-001 ~ TC-H-007
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Header } from '@/components/Header';

// Mock ModeControl 组件
jest.mock('@/components/modes/ModeControl', () => ({
  ModeControl: () => <div data-testid="mode-control">ModeControl Mock</div>,
}));

describe('Header 组件测试', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * TC-H-001: Logo 和标题显示
   */
  describe('TC-H-001: Logo 和标题显示', () => {
    it('应该显示蓝色 "DA" Logo', () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        json: () => Promise.resolve({ session_id: 'test-session-123', export_dir: '/tmp' }),
      });

      render(<Header />);

      const logo = screen.getByText('DA');
      expect(logo).toBeInTheDocument();
      expect(logo).toHaveClass('bg-blue-600');
    });

    it('应该显示 "Data Agent" 标题', () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        json: () => Promise.resolve({ session_id: 'test-session-123', export_dir: '/tmp' }),
      });

      render(<Header />);

      expect(screen.getByText('Data Agent')).toBeInTheDocument();
    });
  });

  /**
   * TC-H-002: 会话 ID 显示
   */
  describe('TC-H-002: 会话 ID 显示', () => {
    it('应该显示会话 ID 的最后 8 位', async () => {
      const sessionId = 'session-abcd1234efgh5678';
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        json: () => Promise.resolve({ session_id: sessionId, export_dir: '/tmp' }),
      });

      render(<Header />);

      await waitFor(() => {
        expect(screen.getByText('会话: efgh5678')).toBeInTheDocument();
      });
    });

    it('应该在会话加载前不显示会话信息', () => {
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {})); // 永不解析

      render(<Header />);

      expect(screen.queryByText(/会话:/)).not.toBeInTheDocument();
    });
  });

  /**
   * TC-H-003: 数据库已连接状态
   */
  describe('TC-H-003: 数据库连接状态显示', () => {
    it('应该显示绿色连接状态指示器', () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        json: () => Promise.resolve({ session_id: 'test', export_dir: '/tmp' }),
      });

      render(<Header />);

      const indicator = document.querySelector('.bg-green-500');
      expect(indicator).toBeInTheDocument();
    });

    it('应该显示 "已连接" 文字', () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        json: () => Promise.resolve({ session_id: 'test', export_dir: '/tmp' }),
      });

      render(<Header />);

      expect(screen.getByText('已连接')).toBeInTheDocument();
    });
  });

  /**
   * TC-H-005: 模式设置按钮点击
   */
  describe('TC-H-005: 模式设置按钮点击', () => {
    it('点击按钮应该显示模式设置面板', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        json: () => Promise.resolve({ session_id: 'test', export_dir: '/tmp' }),
      });

      render(<Header />);

      const button = screen.getByText('模式设置');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByTestId('mode-control')).toBeInTheDocument();
      });
    });
  });

  /**
   * TC-H-006: 模式设置面板关闭
   */
  describe('TC-H-006: 模式设置面板关闭', () => {
    it('点击关闭按钮应该隐藏面板', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        json: () => Promise.resolve({ session_id: 'test', export_dir: '/tmp' }),
      });

      render(<Header />);

      // 打开面板
      fireEvent.click(screen.getByText('模式设置'));

      await waitFor(() => {
        expect(screen.getByTestId('mode-control')).toBeInTheDocument();
      });

      // 关闭面板
      fireEvent.click(screen.getByText('✕'));

      await waitFor(() => {
        expect(screen.queryByTestId('mode-control')).not.toBeInTheDocument();
      });
    });
  });

  /**
   * TC-H-007: 会话信息加载失败
   */
  describe('TC-H-007: 会话信息加载失败', () => {
    it('API 失败时不应显示会话 ID，页面不崩溃', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<Header />);

      // 页面应该正常渲染
      expect(screen.getByText('Data Agent')).toBeInTheDocument();

      // 不应显示会话信息
      await waitFor(() => {
        expect(screen.queryByText(/会话:/)).not.toBeInTheDocument();
      });
    });
  });
});
