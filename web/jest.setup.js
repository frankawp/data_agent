import '@testing-library/jest-dom';

// Mock fetch API
global.fetch = jest.fn();

// Mock scrollIntoView
Element.prototype.scrollIntoView = jest.fn();

// 重置所有 mock
beforeEach(() => {
  jest.clearAllMocks();
});
