"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  fetchCriticalAlertMap,
  fetchUnlocatedCriticalAlerts,
  getAuthToken,
  WS_BASE
} from "@/lib/api/alert";
import { CriticalAlertMapCacheSchema } from "@/lib/validators/alert";

import type {
  CriticalAlertMapCache,
  CriticalAlertMapItem,
  UnlocatedCriticalAlertItem,
} from "@/lib/validators/alert";


const CACHE_VERSION = 1 as const;
const RECONNECT_DELAYS_MS = 3_000;

function getCacheKey(
  neighbourhoodId: string
) : string {
  return (
    "watchdog:critical-alert-map:" + neighbourhoodId
  );
}

export function useCriticalAlerts(
  neighbourhoodId: string,
) {
  const [mappedAlerts, setMappedAlerts] = useState<CriticalAlertMapItem[]>([]);

  const [unlocatedAlerts, setUnlocatedAlerts] = useState<UnlocatedCriticalAlertItem[]>([]);

  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isOnline, setIsOnline] =
  useState<boolean>(() => {
    if (typeof navigator === "undefined") {
      return true;
    }

    return navigator.onLine;
  });

  const [wsConnected, setWsConnected] = useState(false);

  const [usingCachedData, setUsingCachedData] = useState(false);

  const websocketRef = useRef<WebSocket | null>(null);

  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const writeCache = useCallback(
    (
      mapped: CriticalAlertMapItem[],
      unlocated:
        UnlocatedCriticalAlertItem[],
      updatedAt: string,
    ) => {
      if (!neighbourhoodId) {
        return;
      }

      const cacheState = {
        version: CACHE_VERSION,
        mapped_alerts: mapped,
        unlocated_alerts: unlocated,
        last_updated: updatedAt,
        cached_at: new Date().toISOString(),
      };

      try {
        localStorage.setItem(
          getCacheKey(neighbourhoodId),
          JSON.stringify(cacheState),
        );
      } catch {
        // Cache failure must not break the live map.
      }
    },
    [neighbourhoodId]
  );

   const readCache = useCallback((): boolean => {
    if (!neighbourhoodId) {
      return false;
    }

    const key = getCacheKey(neighbourhoodId);

    try {
      const stored = localStorage.getItem(key);

      if (!stored) {
        return false;
      }

      const parsed =
        CriticalAlertMapCacheSchema.safeParse(
          JSON.parse(stored),
        );

      if (!parsed.success) {
        localStorage.removeItem(key);
        return false;
      }

      // Only open alerts belong on this map.
      const mapped =
        parsed.data.mapped_alerts.filter(
          (alert) =>
            alert.status === "OPEN",
        );

      const unlocated =
        parsed.data.unlocated_alerts.filter(
          (alert) =>
            alert.status === "OPEN",
        );

      setMappedAlerts(mapped);
      setUnlocatedAlerts(unlocated);
      setLastUpdated(
        parsed.data.last_updated,
      );
      setUsingCachedData(true);

      return true;
    } catch {
      localStorage.removeItem(key);
      return false;
    }
  }, [neighbourhoodId]);

  const reconcile = useCallback(
    async (showLoading = false) => {
      if (!neighbourhoodId) {
        return;
      }

      if (showLoading) {
        setLoading(true);
      }

      setError(null);

      try {
        const [
          mapResponse,
          unlocatedResponse,
        ] = await Promise.all([
          fetchCriticalAlertMap(
            neighbourhoodId,
          ),
          fetchUnlocatedCriticalAlerts(
            neighbourhoodId,
          ),
        ]);

        const mapped =
          mapResponse.data.alerts.filter(
            (alert) =>
              alert.status === "OPEN",
          );

        const unlocated =
          unlocatedResponse.data.alerts.filter(
            (alert) =>
              alert.status === "OPEN",
          );

        const updatedAt = mapResponse.data.last_updated;

        setMappedAlerts(mapped);
        setUnlocatedAlerts(unlocated);
        setLastUpdated(updatedAt);
        setUsingCachedData(false);

        writeCache(
          mapped,
          unlocated,
          updatedAt,
        );
      } catch (caughtError) {
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "Failed to retrieve critical alerts",
        );

        // Keep the existing/cache state visible.
        setUsingCachedData(true);
      } finally {
        if (showLoading) {
          setLoading(false);
        }
      }
    },
    [
      neighbourhoodId,
      writeCache,
    ],
  );
 

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
