import React from "react";
import "@testing-library/jest-dom";
import {
  act,
  render,
  screen,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import AlertsPage from "@/app/alert/page";
import * as api from "@/lib/api/alert";
import { mockAlert } from "../fixtures/alert";

jest.mock("next/navigation", () => ({
  useSearchParams: () => ({
    get: () => null,
  }),
}));

jest.mock("@/lib/api/alert", () => ({
  fetchCurrentUser: jest.fn(),
  fetchAlerts: jest.fn(),
  acknowledgeAlert: jest.fn(),
  normaliseAlert: (raw: Record<string, unknown>) => ({
    ...raw,
    status: raw.status === "OPEN" ? "NEW" : raw.status,
  }),
  getAuthToken: () => "test-token",
  WS_BASE: "ws://localhost:8000",
  ApiError: class ApiError extends Error {
    statusCode?: number;

    constructor(message: string, statusCode?: number) {
      super(message);
      this.name = "ApiError";
      this.statusCode = statusCode;
    }
  },
}));

const mocked = api as jest.Mocked<typeof api>;

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  url: string;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    queueMicrotask(() => this.onopen?.());
  }

  close() {
    this.onclose?.();
  }

  static reset() {
    MockWebSocket.instances = [];
  }

  static emit(payload: unknown) {
    const data =
      typeof payload === "string" ? payload : JSON.stringify(payload);
    for (const instance of MockWebSocket.instances) {
      instance.onmessage?.({ data });
    }
  }
}

(globalThis as any).WebSocket = MockWebSocket;

describe("AlertsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    MockWebSocket.reset();
  });

  it("loads alerts and acknowledges one alert", async () => {
    mocked.fetchCurrentUser.mockResolvedValue({
      neighbourhood_id: "n-1",
    } as any);
    mocked.fetchAlerts.mockResolvedValue([mockAlert] as any);
    mocked.acknowledgeAlert.mockResolvedValue(undefined as any);

    render(<AlertsPage />);

    expect(await screen.findByText(/alerts/i)).toBeInTheDocument();

    const ack = await screen.findByRole("button", {
      name: /acknowledge alert/i,
    });
    fireEvent.click(ack);

    await waitFor(() => {
      expect(mocked.acknowledgeAlert).toHaveBeenCalledWith(mockAlert.id);
    });

    await waitFor(() => {
      expect(screen.getByText(/acknowledged/i)).toBeInTheDocument();
    });
  });

  it("accepts websocket alert.new messages", async () => {
    mocked.fetchCurrentUser.mockResolvedValue({
      neighbourhood_id: "n-1",
    } as any);
    mocked.fetchAlerts.mockResolvedValue([] as any);

    render(<AlertsPage />);

    await waitFor(() => {
      expect(screen.getByText(/no alerts/i)).toBeInTheDocument();
    });

    act(() => {
      MockWebSocket.emit({ event: "alert.new", payload: mockAlert });
    });

    await screen.findByText(/person detected/i);
  });
});
