import {
  Granularities,
  NeighbourhoodRiskScoreRes,
  NeighbourhoodRiskScoreHistory,
} from "../validators/riskScore";
import { apiCall } from "./client";

export async function fetchNeighbourhoodRiskScore(
  neighbourhoodId: string,
): Promise<NeighbourhoodRiskScoreRes> {
  const url = `/risk-score/neighbourhood/${neighbourhoodId}`;

  return await apiCall<NeighbourhoodRiskScoreRes>(url, { method: "GET" });
}

export async function fetchNeighbourhoodRiskScoreHistory(
  neighbourhoodId: string,
  granularity: Granularities,
  start?: string,
  end?: string,
): Promise<NeighbourhoodRiskScoreHistory> {
  const params = new URLSearchParams({ granularity });
  if (start) params.set("start", start);
  if (end) params.set("end", end);

  const url = `/risk-score/neighbourhood/${neighbourhoodId}/history?${params}`;

  return await apiCall<NeighbourhoodRiskScoreHistory>(url, { method: "GET" });
}
