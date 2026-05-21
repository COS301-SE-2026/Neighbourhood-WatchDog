import type { Alert, AlertStatus } from "@/components/shared/AlertCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const WS_BASE = API_BASE.replace(/^http/, "ws");

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const token = getAuthToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
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
