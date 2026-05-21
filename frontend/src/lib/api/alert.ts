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

export async function fetchAlerts(
  neighbourhoodId: string,
  signal?: AbortSignal,
): Promise<Alert[]> {
  const res = await apiFetch<{
    status: number;
    data: Record<string, unknown>[];
  }>(`/alerts/${neighbourhoodId}`, { signal });
  return (res.data ?? []).map(normaliseAlert);
}

export async function acknowledgeAlert(alertId: string): Promise<void> {
  await apiFetch(`/alerts/${alertId}/acknowledge`, { method: "PATCH" });
}
