/**
 * DataTable 组件测试
 * 覆盖测试用例: TC-DT-001 ~ TC-DT-006
 */
import { render, screen } from '@testing-library/react';
import { DataTable } from '@/components/data-display/DataTable';

describe('DataTable 组件测试', () => {
  /**
   * TC-DT-001: 空数据显示
   */
  describe('TC-DT-001: 空数据显示', () => {
    it('columns 为空时应该显示 "无数据"', () => {
      render(<DataTable data={{ columns: [], rows: [] }} />);

      expect(screen.getByText('无数据')).toBeInTheDocument();
    });
  });

  /**
   * TC-DT-002: 表头显示
   */
  describe('TC-DT-002: 表头显示', () => {
    it('应该正确显示表头列名', () => {
      const data = {
        columns: ['ID', 'Name', 'Email'],
        rows: [['1', 'John', 'john@example.com']],
      };

      render(<DataTable data={data} />);

      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
    });

    it('表头应该有灰色背景', () => {
      const data = {
        columns: ['ID'],
        rows: [['1']],
      };

      render(<DataTable data={data} />);

      const thead = document.querySelector('thead');
      expect(thead).toHaveClass('bg-gray-50');
    });

    it('列名应该大写显示', () => {
      const data = {
        columns: ['name'],
        rows: [['John']],
      };

      render(<DataTable data={data} />);

      const th = screen.getByText('name');
      expect(th).toHaveClass('uppercase');
    });
  });

  /**
   * TC-DT-003: 数据行显示
   */
  describe('TC-DT-003: 数据行显示', () => {
    it('应该正确显示所有数据行', () => {
      const data = {
        columns: ['ID', 'Name'],
        rows: [
          ['1', 'Alice'],
          ['2', 'Bob'],
          ['3', 'Charlie'],
        ],
      };

      render(<DataTable data={data} />);

      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('Bob')).toBeInTheDocument();
      expect(screen.getByText('Charlie')).toBeInTheDocument();
    });

    it('行与行之间应该有分隔线', () => {
      const data = {
        columns: ['ID'],
        rows: [['1'], ['2']],
      };

      render(<DataTable data={data} />);

      const tbody = document.querySelector('tbody');
      expect(tbody).toHaveClass('divide-y');
    });
  });

  /**
   * TC-DT-004: 行悬停效果
   */
  describe('TC-DT-004: 行悬停效果', () => {
    it('数据行应该有 hover 样式类', () => {
      const data = {
        columns: ['ID'],
        rows: [['1']],
      };

      render(<DataTable data={data} />);

      const tr = document.querySelector('tbody tr');
      expect(tr).toHaveClass('hover:bg-gray-50');
    });
  });

  /**
   * TC-DT-005: 行数统计显示
   */
  describe('TC-DT-005: 行数统计显示', () => {
    it('有数据时应该显示行数统计', () => {
      const data = {
        columns: ['ID'],
        rows: [['1'], ['2'], ['3']],
      };

      render(<DataTable data={data} />);

      expect(screen.getByText('共 3 行')).toBeInTheDocument();
    });

    it('单行数据也应该显示统计', () => {
      const data = {
        columns: ['ID'],
        rows: [['1']],
      };

      render(<DataTable data={data} />);

      expect(screen.getByText('共 1 行')).toBeInTheDocument();
    });

    it('无数据时不应显示行数统计', () => {
      const data = {
        columns: ['ID'],
        rows: [],
      };

      render(<DataTable data={data} />);

      expect(screen.queryByText(/共.*行/)).not.toBeInTheDocument();
    });
  });

  /**
   * TC-DT-006: 水平滚动
   */
  describe('TC-DT-006: 水平滚动', () => {
    it('表格容器应该有 overflow-auto 类', () => {
      const data = {
        columns: ['ID'],
        rows: [['1']],
      };

      render(<DataTable data={data} />);

      const container = document.querySelector('.overflow-auto');
      expect(container).toBeInTheDocument();
    });
  });

  /**
   * 边界情况测试
   */
  describe('边界情况', () => {
    it('应该正确处理空字符串单元格', () => {
      const data = {
        columns: ['ID', 'Name'],
        rows: [['1', '']],
      };

      render(<DataTable data={data} />);

      // 不应崩溃，表格应该正常渲染
      expect(screen.getByText('ID')).toBeInTheDocument();
    });

    it('应该正确处理特殊字符', () => {
      const data = {
        columns: ['Name'],
        rows: [['<script>alert("xss")</script>']],
      };

      render(<DataTable data={data} />);

      // React 自动转义，不应执行脚本
      expect(screen.getByText('<script>alert("xss")</script>')).toBeInTheDocument();
    });
  });
});
