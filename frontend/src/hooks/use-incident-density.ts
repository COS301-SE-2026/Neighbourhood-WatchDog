import {
  useEffect,
  useState,
} from "react";

import { fetchIncidentDensity } from "@/lib/api/incident-density";
import type {
  IncidentDensityData,
  IncidentDensityViewport,
} from "@/lib/validators/incident-density";

const FETCH_DEBOUNCE_MS = 350;

interface UseIncidentDensityOptions {
  neighbourhoodId: string;
  startDate: string;
  endDate: string;
  viewport: IncidentDensityViewport | null;
  enabled: boolean;
}

interface UseIncidentDensityResult {
  data: IncidentDensityData | null;
  loading: boolean;
  error: string | null;
}

export function useIncidentDensity({
  neighbourhoodId,
  startDate,
  endDate,
  viewport,
  enabled,
}: UseIncidentDensityOptions): UseIncidentDensityResult {
  const [data, setData] = useState<IncidentDensityData | null>(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

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
            await fetchIncidentDensity(
              neighbourhoodId,
              {
                startDate,
                endDate,
                ...viewport,
              },
            );

          if (!cancelled) {
            setData(result);
          }
        } catch (requestError) {
          if (!cancelled) {
            setError(
              requestError instanceof Error
                ? requestError.message
                : "Unable to load incident density",
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
    startDate,
    endDate,
    viewport,
  ]);

  return {
    data: requestEnabled ? data : null,
    loading: requestEnabled ? loading : false,
    error: requestEnabled ? error : null,
  };
}
