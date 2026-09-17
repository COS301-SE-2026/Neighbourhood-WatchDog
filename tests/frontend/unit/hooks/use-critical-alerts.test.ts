import {
  act,
  cleanup,
  renderHook,
  waitFor,
} from "@testing-library/react";

import {
  fetchCriticalAlertMap,
  fetchUnlocatedCriticalAlerts,
} from "@/lib/api/alert";
import { useCriticalAlerts } from "@/hooks/use-critical-alerts";

import type {
  CriticalAlertMapItem,
  CriticalAlertMapRes,
  UnlocatedCriticalAlertsRes,
} from "@/lib/validators/alert";


jest.mock("@/lib/api/alert", () => ({
  fetchCriticalAlertMap: jest.fn(),
  fetchUnlocatedCriticalAlerts: jest.fn(),
  getAuthToken: jest.fn(
    () => "test-access-token",
  ),
  WS_BASE: "ws://localhost:8000",
}));

const NEIGHBOURHOOD_ID = "40a3036a-99ed-455f-891b-166826ff0886";

const CACHE_KEY = `watchdog:critical-alert-map:${NEIGHBOURHOOD_ID}`;

const LAST_UPDATED = "2026-09-17T10:00:00.000Z";

const MAPPED_ALERT: CriticalAlertMapItem = {
  id: "11111111-1111-4111-8111-111111111111",
  camera_id: "22222222-2222-4222-8222-222222222222",
  camera_name: "Front Gate Camera",
  neighbourhood_id: NEIGHBOURHOOD_ID,
  detection_type: "WEAPON_DETECTED",
  status: "OPEN",
  created_at: LAST_UPDATED,
  property_id: "33333333-3333-4333-8333-333333333333",
  property_address: "123 Test Street, Pretoria",
  thumbnail_url: null,
  latitude: -25.7479,
  longitude: 28.2293,
};

const SECOND_ALERT: CriticalAlertMapItem = {
  ...MAPPED_ALERT,
  id: "44444444-4444-4444-8444-444444444444",
  detection_type: "FALL_DETECTED",
};

function mapResponse(
  alerts: CriticalAlertMapItem[],
): CriticalAlertMapRes {
  return {
    status: 200,
    message: "Alerts retrieved",
    data: {
      alerts,
      last_updated: LAST_UPDATED,
    },
  };
}

function unlocatedResponse(): UnlocatedCriticalAlertsRes {
  return {
    status: 200,
    message: "Alerts retrieved",
    data: {
      alerts: [],
      last_updated: LAST_UPDATED,
    },
  };
}

function setOnline(value: boolean) {
  Object.defineProperty(
    navigator,
    "onLine",
    {
      configurable: true,
      value,
    },
  );
}


class MockWebSocket {
  static instances: MockWebSocket[] = [];

  readonly url: string;

  onopen: WebSocket["onopen"] = null;
  onmessage: WebSocket["onmessage"] = null;
  onerror: WebSocket["onerror"] = null;
  onclose: WebSocket["onclose"] = null;

  constructor(url: string | URL) {
    this.url = String(url);
    MockWebSocket.instances.push(this);
  }

  open() {
    this.onopen?.(
      new Event("open") as Event,
    );
  }

  receive(data: object) {
    this.onmessage?.(
      new MessageEvent("message", {
        data: JSON.stringify(data),
      }),
    );
  }

  disconnect() {
    this.onclose?.(
      new CloseEvent("close"),
    );
  }

  close = jest.fn(() => {
    this.onclose?.(
      new CloseEvent("close"),
    );
  });

  send = jest.fn();
}


const mockFetchMap =
  fetchCriticalAlertMap as jest.MockedFunction<
    typeof fetchCriticalAlertMap
  >;

const mockFetchUnlocated =
  fetchUnlocatedCriticalAlerts as jest.MockedFunction<
    typeof fetchUnlocatedCriticalAlerts
  >;
