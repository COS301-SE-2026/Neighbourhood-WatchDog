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

  test("does not connect without a neighbourhood", () => {
    const { result } = renderHook(() =>
      useDispatchNotification(null),
    );

    expect(MockWebSocket.instances).toHaveLength(0);
    expect(result.current.notification).toBeNull();
  });

  test("shows a dispatch notification and ignores unrelated messages", () => {
    const { result } = renderHook(() =>
      useDispatchNotification(NEIGHBOURHOOD_ID),
    );

    const socket = MockWebSocket.instances[0];

    expect(socket.url).toContain(
      `/alerts/${NEIGHBOURHOOD_ID}/ws?token=test-token`,
    );

    act(() => {
      socket.receiveRaw("invalid JSON");
      socket.receive({ event: "alert.created" });
      socket.receive({ event: "dispatch.notified" });
    });

    expect(result.current.notification).toBeNull();

    act(() => {
      notify(socket);
    });

    expect(result.current.notification).toMatchObject({
      dispatchId: "dispatch-1",
      alertId: "alert-1",
      propertyId: "property-1",
      neighbourhoodId: NEIGHBOURHOOD_ID,
      detectionType: "WEAPON_DETECTED",
      distance: 500,
      eta: 90,
    });
  });

  test.each([
    ["accept", "ACCEPT", "ACCEPTED"],
    ["decline", "DECLINE", "DECLINED"],
  ] as const)(
    "%s calls the API and shows %s outcome",
    async (method, action, expectedOutcome) => {
      const { result } = renderHook(() =>
        useDispatchNotification(NEIGHBOURHOOD_ID),
      );

      act(() => {
        notify(MockWebSocket.instances[0]);
      });

      let succeeded = false;
      await act(async () => {
        succeeded = await result.current[method]();
      });

      expect(succeeded).toBe(true);
      expect(mockRespond).toHaveBeenCalledWith(
        "dispatch-1",
        action,
      );
      expect(result.current.notification).toBeNull();
      expect(result.current.outcome).toBe(expectedOutcome);
      expect(result.current.responding).toBe(false);
    },
  );

  test("treats an expired dispatch response as expired", async () => {
    mockRespond.mockRejectedValue(
      new ApiError("Already assigned", 409),
    );

    const { result } = renderHook(() =>
      useDispatchNotification(NEIGHBOURHOOD_ID),
    );

    act(() => {
      notify(MockWebSocket.instances[0]);
    });

    await act(async () => {
      expect(await result.current.accept()).toBe(false);
    });

    expect(result.current.outcome).toBe("EXPIRED");
    expect(result.current.notification).toBeNull();
    expect(toast.error).not.toHaveBeenCalled();
  });
});
