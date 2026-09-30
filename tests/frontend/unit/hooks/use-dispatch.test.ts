import {
  act,
  cleanup,
  renderHook,
} from "@testing-library/react";
import { toast } from "sonner";

import { ApiError } from "@/lib/api/alert";
import { respondToDispatch } from "@/lib/api/dispatch";
import { getAccessToken, refreshSession } from "@/lib/auth/cognito";
import { useDispatchNotification } from "@/hooks/use-dispatch";

jest.mock("@/lib/api/alert", () => ({
  WS_BASE: "ws://localhost:8000",
  ApiError: class extends Error {
    constructor(
      message: string,
      public statusCode?: number,
    ) {
      super(message);
    }
  },
}));

jest.mock("@/lib/api/dispatch", () => ({
  respondToDispatch: jest.fn(),
}));

jest.mock("@/lib/auth/cognito", () => ({
  getAccessToken: jest.fn(),
  refreshSession: jest.fn(),
}));

jest.mock("sonner", () => ({
  toast: { error: jest.fn() },
}));

const NEIGHBOURHOOD_ID = "neighbourhood-1";

const mockGetAccessToken =
  getAccessToken as jest.MockedFunction<typeof getAccessToken>;
const mockRefreshSession =
  refreshSession as jest.MockedFunction<typeof refreshSession>;
const mockRespond =
  respondToDispatch as jest.MockedFunction<typeof respondToDispatch>;

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  close = jest.fn();

  constructor(readonly url: string) {
    MockWebSocket.instances.push(this);
  }

  receive(payload: unknown) {
    this.onmessage?.(
      new MessageEvent("message", {
        data: JSON.stringify(payload),
      }),
    );
  }

  receiveRaw(data: string) {
    this.onmessage?.(
      new MessageEvent("message", { data }),
    );
  }

  disconnect() {
    this.onclose?.(new CloseEvent("close"));
  }
}

function notify(
  socket: MockWebSocket,
  overrides: Record<string, unknown> = {},
) {
  socket.receive({
    event: "dispatch.notified",
    payload: {
      dispatch_id: "dispatch-1",
      alert_id: "alert-1",
      property_id: "property-1",
      neighbourhood_id: NEIGHBOURHOOD_ID,
      detection_type: "WEAPON_DETECTED",
      distance: 500,
      eta: 90,
      notified_at: "2026-09-30T10:00:00.000Z",
      ...overrides,
    },
  });
}

describe("useDispatchNotification", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    MockWebSocket.instances = [];

    Object.defineProperty(globalThis, "WebSocket", {
      configurable: true,
      writable: true,
      value: MockWebSocket,
    });

    mockGetAccessToken.mockReturnValue("test-token");
    mockRefreshSession.mockResolvedValue("refreshed-token");
    mockRespond.mockResolvedValue(null);
  });

  afterEach(() => {
    cleanup();
    jest.useRealTimers();
  });


});
