import type { Alert, AlertStatus } from "@/components/shared/AlertCard";
import { getApiBaseUrl, getAuthHeaders } from "@/lib/api/auth";

export { getAuthToken } from "@/lib/api/auth";

const API_BASE = getApiBaseUrl();
export const WS_BASE = API_BASE.replace(/^http/, "ws");

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  let res: Response;

  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: getAuthHeaders(init?.headers ?? {}),
    });
  } catch (error) {
    console.error("API request failed before a response was received", {
      path,
      apiBase: API_BASE,
      method: init?.method ?? "GET",
      error,
    });
    throw new Error(
      `Unable to reach the server for ${path}. Check that the backend is running and CORS is configured.`,
    );
  }

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    console.error("API request returned an error response", {
      path,
      apiBase: API_BASE,
      status: res.status,
      body: text,
    });
    throw new ApiError(`API ${res.status}: ${text}`, res.status);
  }

  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export async function fetchCurrentUser(): Promise<{
  neighbourhood_id: string | null;
}> {
  return apiFetch<{ neighbourhood_id: string | null }>("/auth/me");
}

export function normaliseAlert(raw: Record<string, unknown>): Alert {
  return {
    ...(raw as unknown as Alert),
    status: raw.status === "OPEN" ? "NEW" : (raw.status as AlertStatus),
  };
}

function denormaliseStatus(status: AlertStatus): string {
  return status === "NEW" ? "OPEN" : status;
}

export interface Pagination {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface AlertFilters {
  status?: AlertStatus;
  cameraId?: string;
  detectionType?: string;
  startDate?: Date;
  endDate?: Date;
  limit?: number;
  offset?: number;
}

export interface PaginatedAlerts {
  alerts: Alert[];
  pagination: Pagination;
}

interface ListAlertsRes {
  status: number;
  message: string | null;
  data: Record<string, unknown>[] | null;
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  } | null;
}

function buildAlerts(filters?: AlertFilters): string {
  const parms = new URLSearchParams();

  if (filters?.status) {
    parms.set("status", denormaliseStatus(filters.status));
  }
  if (filters?.cameraId) {
    parms.set("camera_id", filters.cameraId);
  }
  if (filters?.detectionType) {
    parms.set("detection_type", filters.detectionType);
  }
  if (filters?.startDate) {
    parms.set("start_date", filters.startDate.toISOString());
  }
  if (filters?.endDate) {
    parms.set("end_date", filters.endDate.toISOString());
  }
  if (filters?.limit) {
    parms.set("limit", String(filters.limit));
  }
  if (filters?.offset) {
    parms.set("offset", String(filters.offset));
  }

  const query = parms.toString();
  return query ? `?${query}` : "";
}

export async function fetchAlerts(
  neighbourhoodId: string,
  filters?: AlertFilters,
  signal?: AbortSignal,
): Promise<PaginatedAlerts> {
  const query = buildAlerts(filters);
  const res = await apiFetch<ListAlertsRes>(
    `/alerts/${neighbourhoodId}${query}`,
    { signal },
  );

  return {
    alerts: (res.data ?? []).map(normaliseAlert),
    pagination: {
      total: res.pagination?.total ?? 0,
      limit: res.pagination?.limit ?? 25,
      offset: res.pagination?.offset ?? 0,
      has_more: res.pagination?.has_more ?? false,
    },
  };
}

export async function acknowledgeAlert(alertId: string): Promise<void> {
  await apiFetch(`/alerts/${alertId}/acknowledge`, { method: "PATCH" });
}
