"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";
import {
  fetchCriticalAlertMap,
  fetchUnlocatedCriticalAlerts,
} from "@/lib/api/alert";
import type {
  CriticalAlertMapItem,
  UnlocatedCriticalAlertItem,
} from "@/lib/validators/alert";

export function useCriticalAlerts(
  neighbourhoodId: string,
) {
  const [mappedAlerts, setMappedAlerts] = useState<CriticalAlertMapItem[]>([]);

  const [unlocatedAlerts, setUnlocatedAlerts] = useState<UnlocatedCriticalAlertItem[]>([]);

  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    if (!neighbourhoodId) {
      setMappedAlerts([]);
      setUnlocatedAlerts([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [mapResponse, unlocatedResponse] =
        await Promise.all([
          fetchCriticalAlertMap(neighbourhoodId),
          fetchUnlocatedCriticalAlerts(neighbourhoodId),
        ]);

      setMappedAlerts(mapResponse.data.alerts);
      setUnlocatedAlerts(
        unlocatedResponse.data.alerts,
      );
      setLastUpdated(mapResponse.data.last_updated);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Failed to retrieve critical alerts",
      );
    } finally {
      setLoading(false);
    }
  }, [neighbourhoodId]);

  useEffect(() => {
    void fetchAlerts();
  }, [fetchAlerts]);

  return {
    mappedAlerts,
    unlocatedAlerts,
    lastUpdated,
    loading,
    error,
    refetch: fetchAlerts,
  };
}
