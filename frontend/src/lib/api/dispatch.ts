import { apiFetch } from "./alert";

export type DispatchStatus =
  | "SELECTED"
  | "PENDING"
  | "QUEUED"
  | "NOTIFIED"
  | "ACCEPTED"
  | "DECLINED"
  | "TIMED_OUT"
  | "NO_CANDIDATE";

export type DispatchAction = "ACCEPT" | "DECLINE";

export interface DispatchCandidate {
  id: string;
  alert_id: string;
  officer_id: string | null;
  rank: number | null;
  score: number | null;
  distance: number | null;
  eta: number | null;
  workload: number | null;
  status: DispatchStatus;
  officer_availability: string | null;
  is_location_stale: boolean;
  created_at: string;
  notified_at: string | null;
  responded_at: string | null;
}

interface RespondDispatchResponse {
  status: number;
  message: string | null;
  data: DispatchCandidate | null;
}

export async function respondToDispatch(
  dispatchId: string,
  action: DispatchAction,
): Promise<DispatchCandidate | null> {
  const response = await apiFetch<RespondDispatchResponse>(
    `/dispatch/${dispatchId}/respond`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action }),
    },
  );

  return response.data;
}

export interface DispatchRecord {
  id: string;
  alert_id: string;
  triggering_sighting_id: string | null;
  officer_id: string | null;
  rank: number | null;
  score: number | null;
  distance: number | null;
  eta: number | null;
  workload: number | null;
  status: DispatchStatus;
  officer_availability: string | null;
  is_location_stale: boolean;
  created_at: string;
  notified_at: string | null;
  responded_at: string | null;
}

export interface DispatchPage {
  total: number;
  page: number;
  size: number;
  results: DispatchRecord[];
}

export interface DispatchListFilters {
  status: DispatchStatus | "ALL";
  search: string;
  from: string;
  to: string;
  sort: "NEWEST" | "OLDEST";
}

interface DispatchListResponse {
  data: DispatchPage;
}

export async function listNeighbourhoodDispatches(
  neighbourhoodId: string,
  page: number,
  size: number,
  filters: DispatchListFilters,
): Promise<DispatchPage> {
  const params = new URLSearchParams({
    page: String(page),
    size: String(size),
    sort_order: filters.sort === "NEWEST" ? "DESC" : "ASC",
  });

  if (filters.status !== "ALL") {
    params.set("status", filters.status);
  }

  if (filters.search.trim()) {
    params.set("search_term", filters.search.trim());
  }

  if (filters.from) {
    params.set(
      "start_date",
      new Date(`${filters.from}T00:00:00`).toISOString(),
    );
  }

  if (filters.to) {
    params.set(
      "end_date",
      new Date(`${filters.to}T23:59:59.999`).toISOString(),
    );
  }

  const res = await apiFetch<DispatchListResponse>(
    `/dispatch/neighbourhood/${neighbourhoodId}?${params.toString()}`,
  );

  return res.data;
}
