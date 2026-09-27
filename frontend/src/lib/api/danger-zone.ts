import { apiCall } from "@/lib/api/client";

import {
  DangerZoneResponseSchema,
  type DangerZoneData,
  type DangerZoneViewport,
} from "@/lib/validators/danger-zone";

export async function fetchDangerZones(
  neighbourhoodId: string,
  viewport: DangerZoneViewport,
): Promise<DangerZoneData> {
  const query = new URLSearchParams({
    west: String(viewport.west),
    south: String(viewport.south),
    east: String(viewport.east),
    north: String(viewport.north),
  });

  const result = await apiCall<unknown>(
    `/alerts/neighbourhoods/${neighbourhoodId}` +
      `/danger-zones?${query.toString()}`,
  );

  return DangerZoneResponseSchema.parse(
    result,
  ).data;
}