import { apiCall } from "@/lib/api/client";
import {
  IncidentDensityResponseSchema,
  type IncidentDensityData,
  type IncidentDensityViewport,
} from "@/lib/validators/incident-density";

export interface FetchIncidentDensityParams
  extends IncidentDensityViewport {
  startDate: string;
  endDate: string;
}

export async function fetchIncidentDensity(
  neighbourhoodId: string,
  params: FetchIncidentDensityParams,
): Promise<IncidentDensityData> {
  const query = new URLSearchParams({
    start_date: params.startDate,
    end_date: params.endDate,
    west: String(params.west),
    south: String(params.south),
    east: String(params.east),
    north: String(params.north)
  });

  const result = await apiCall<unknown>(
    `/alerts/neighbourhoods/${neighbourhoodId}/incident-density?` + query.toString(),
  );

  return IncidentDensityResponseSchema.parse(
    result,
  ).data;
}
