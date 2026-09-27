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
