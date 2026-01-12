const nextJest = require('next/jest');

const createJestConfig = nextJest({
  // 指向 Next.js 应用的路径
  dir: './',
});

// Jest 自定义配置
const customJestConfig = {
  // 测试环境
  testEnvironment: 'jsdom',

  // 设置测试环境前运行的脚本
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // 模块路径映射
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },

  // 测试文件匹配模式
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{spec,test}.{js,jsx,ts,tsx}',
  ],

  // 忽略的路径
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/.next/',
  ],

  // 收集覆盖率的文件
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/__tests__/**',
  ],
};

module.exports = createJestConfig(customJestConfig);
