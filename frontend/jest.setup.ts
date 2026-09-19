import "@testing-library/jest-dom";

// Mock fetch globally
global.fetch = jest.fn() as jest.Mock;

// Radix UI uses ResizeObserver, which jsdom does not provide.
class MockResizeObserver implements ResizeObserver {
  observe(_target: Element, _options?: ResizeObserverOptions): void {}

  unobserve(_target: Element): void {}

  disconnect(): void {}
}

Object.defineProperty(globalThis, "ResizeObserver", {
  configurable: true,
  writable: true,
  value: MockResizeObserver,
});

// Reset mocks before each test
beforeEach(() => {
  (fetch as jest.Mock).mockReset();
});
