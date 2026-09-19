import "@testing-library/jest-dom";

// Mock fetch globally
global.fetch = jest.fn() as jest.Mock;

// Radix UI uses ResizeObserver, which jsdom does not provide.
class MockResizeObserver implements ResizeObserver {
  private readonly observedTargets = new Set<Element>();

  observe(target: Element, options?: ResizeObserverOptions): void {
    this.observedTargets.add(target);
    void options;
  }

  unobserve(target: Element): void {
    this.observedTargets.delete(target);
  }

  disconnect(): void {
    this.observedTargets.clear();
  }
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
