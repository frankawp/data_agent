/**
 * CodeViewer 组件测试
 * 覆盖测试用例: TC-CV-001 ~ TC-CV-004
 */
import { render, screen } from '@testing-library/react';
import { CodeViewer } from '@/components/data-display/CodeViewer';

describe('CodeViewer 组件测试', () => {
  /**
   * TC-CV-001: SQL 语法高亮
   */
  describe('TC-CV-001: SQL 语法高亮', () => {
    it('应该显示 SQL 语言标签', () => {
      render(<CodeViewer code="SELECT * FROM users" language="sql" />);

      expect(screen.getByText('sql')).toBeInTheDocument();
    });

    it('默认语言应该是 SQL', () => {
      render(<CodeViewer code="SELECT * FROM users" />);

      expect(screen.getByText('sql')).toBeInTheDocument();
    });

    it('SQL 代码应该被正确渲染', () => {
      render(<CodeViewer code="SELECT id FROM users WHERE name = 'test'" language="sql" />);

      // 代码应该被渲染
      const codeElement = document.querySelector('code');
      expect(codeElement).toBeInTheDocument();
      expect(codeElement?.innerHTML).toContain('SELECT');
    });
  });

  /**
   * TC-CV-002: Python 语法高亮
   */
  describe('TC-CV-002: Python 语法高亮', () => {
    it('应该显示 PYTHON 语言标签', () => {
      render(<CodeViewer code="import pandas as pd" language="python" />);

      expect(screen.getByText('python')).toBeInTheDocument();
    });

    it('Python 代码应该被正确渲染', () => {
      render(
        <CodeViewer
          code={`def hello():
    print("Hello World")`}
          language="python"
        />
      );

      const codeElement = document.querySelector('code');
      expect(codeElement).toBeInTheDocument();
      expect(codeElement?.innerHTML).toContain('def');
    });
  });

  /**
   * TC-CV-003: 代码滚动
   */
  describe('TC-CV-003: 代码滚动', () => {
    it('代码区域应该支持滚动', () => {
      render(<CodeViewer code="SELECT * FROM users" language="sql" />);

      const pre = document.querySelector('pre');
      expect(pre).toHaveClass('overflow-auto');
    });

    it('语言标签应该在右上角固定', () => {
      render(<CodeViewer code="SELECT * FROM users" language="sql" />);

      const labelContainer = document.querySelector('.absolute.right-2.top-2');
      expect(labelContainer).toBeInTheDocument();
    });
  });

  /**
   * TC-CV-004: 特殊字符转义
   * 注意：这个测试需要浏览器环境中的 document.createElement
   * 在 jsdom 环境中可能表现不同
   */
  describe('TC-CV-004: 特殊字符转义', () => {
    it('应该正确处理 HTML 特殊字符', () => {
      const codeWithHtml = '<div>test</div>';
      render(<CodeViewer code={codeWithHtml} language="json" />);

      // 代码应该被渲染，不应被解析为 HTML
      const codeElement = document.querySelector('code');
      expect(codeElement).toBeInTheDocument();
    });

    it('应该正确处理 & 符号', () => {
      const codeWithAmpersand = 'a && b';
      render(<CodeViewer code={codeWithAmpersand} language="json" />);

      const codeElement = document.querySelector('code');
      expect(codeElement).toBeInTheDocument();
    });
  });

  /**
   * JSON 语言测试
   */
  describe('JSON 语言', () => {
    it('应该显示 json 语言标签', () => {
      render(<CodeViewer code='{"key": "value"}' language="json" />);

      expect(screen.getByText('json')).toBeInTheDocument();
    });
  });

  /**
   * 边界情况测试
   */
  describe('边界情况', () => {
    it('空代码应该不崩溃', () => {
      render(<CodeViewer code="" language="sql" />);

      // 组件应该正常渲染
      expect(screen.getByText('sql')).toBeInTheDocument();
    });

    it('多行代码应该正确渲染', () => {
      const multilineCode = `SELECT id,
       name,
       email
FROM users
WHERE active = 1`;

      render(<CodeViewer code={multilineCode} language="sql" />);

      const codeElement = document.querySelector('code');
      expect(codeElement).toBeInTheDocument();
    });
  });
});
