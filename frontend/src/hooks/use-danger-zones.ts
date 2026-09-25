import {
  useEffect,
  useState,
} from "react";

import { fetchDangerZones } from "@/lib/api/danger-zone";

import type {
  DangerZoneData,
  DangerZoneViewport,
} from "@/lib/validators/danger-zone";

const FETCH_DEBOUNCE_MS = 350;

interface UseDangerZonesOptions {
  neighbourhoodId: string;
  viewport: DangerZoneViewport | null;
  enabled: boolean;
}

interface UseDangerZonesResult {
  data: DangerZoneData | null;
  loading: boolean;
  error: string | null;
}

export function useDangerZones({
  neighbourhoodId,
  viewport,
  enabled,
}: UseDangerZonesOptions): UseDangerZonesResult {
  const [data, setData] =
    useState<DangerZoneData | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const requestEnabled =
    enabled &&
    neighbourhoodId.length > 0 &&
    viewport !== null;

  useEffect(() => {
    if (!requestEnabled || !viewport) {
      return;
    }

    let cancelled = false;

    const timer = window.setTimeout(
      async () => {
        setLoading(true);
        setError(null);

        try {
          const result =
            await fetchDangerZones(
              neighbourhoodId,
              viewport,
            );

          if (!cancelled) {
            setData(result);
          }
        } catch (requestError) {
          if (!cancelled) {
            setError(
              requestError instanceof Error
                ? requestError.message
                : "Unable to load danger zones",
            );
          }
        } finally {
          if (!cancelled) {
            setLoading(false);
          }
        }
      },
      FETCH_DEBOUNCE_MS,
    );

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [
    requestEnabled,
    neighbourhoodId,
    viewport,
  ]);

  return {
    data: requestEnabled ? data : null,
    loading: requestEnabled ? loading : false,
    error: requestEnabled ? error : null,
  };
}