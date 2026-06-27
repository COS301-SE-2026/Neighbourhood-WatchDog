import "@testing-library/jest-dom";

// Mock fetch globally
global.fetch = jest.fn() as jest.Mock;

// Reset mocks before each test
beforeEach(() => {
  (fetch as jest.Mock).mockReset();
});