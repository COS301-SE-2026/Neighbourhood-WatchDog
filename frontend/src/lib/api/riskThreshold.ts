import { apiCall } from "./client";
import {
  NeighbourhoodRiskThresholdConfigRes,
  UpdateRiskThresholdConfigReq,
} from "../validators/riskThreshold";

export async function fetchNeighbourhoodRiskThreshold(
  neighbourhoodId: string,
): Promise<NeighbourhoodRiskThresholdConfigRes> {
  const url = `/risk-threshold/neighbourhood/${neighbourhoodId}`;

  return await apiCall<NeighbourhoodRiskThresholdConfigRes>(url, {
    method: "GET",
  });
}

export async function updateNeighbourhoodRiskThreshold(
  neighbourhoodId: string,
  data: UpdateRiskThresholdConfigReq,
): Promise<NeighbourhoodRiskThresholdConfigRes> {
  const url = `/risk-threshold/neighbourhood/${neighbourhoodId}`;

  return await apiCall<NeighbourhoodRiskThresholdConfigRes>(url, {
    method: "PATCH",
    body: data,
  });
}
