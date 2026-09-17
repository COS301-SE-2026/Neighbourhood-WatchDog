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
  CriticalAlertMapItem,
  UnlocatedCriticalAlertItem,
} from "@/lib/validators/alert";


const CACHE_VERSION = 1 as const;
const RECONNECT_DELAY_MS = 3_000;

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


  // Load cache immediately, then obtain fresh state.
  useEffect(() => {
    if (!neighbourhoodId) {
      setMappedAlerts([]);
      setUnlocatedAlerts([]);
      setLastUpdated(null);
      setUsingCachedData(false);
      setLoading(false);
      return;
    }

    const cacheLoaded = readCache();

    if (cacheLoaded) {
      setLoading(false);
    }

    if (navigator.onLine) {
      void reconcile(!cacheLoaded);
    }
  }, [
    neighbourhoodId,
    readCache,
    reconcile,
  ]);

  // Detect browser online/offline changes.
  useEffect(() => {
    function handleOnline() {
      setIsOnline(true);

      // Reconcile anything missed while offline.
      void reconcile(false);
    }

    function handleOffline() {
      setIsOnline(false);
      setWsConnected(false);

      websocketRef.current?.close();
    }

    window.addEventListener(
      "online",
      handleOnline,
    );

    window.addEventListener(
      "offline",
      handleOffline,
    );

    return () => {
      window.removeEventListener(
        "online",
        handleOnline,
      );

      window.removeEventListener(
        "offline",
        handleOffline,
      );
    };
  }, [reconcile]);

  // Connect and automatically reconnect WebSocket.
  useEffect(() => {
    if (!neighbourhoodId || !isOnline) {
      return;
    }

    let disposed = false;

    function scheduleReconnect() {
      if (
        disposed ||
        !navigator.onLine
      ) {
        return;
      }

      reconnectTimerRef.current =
        setTimeout(
          connect,
          RECONNECT_DELAY_MS,
        );
    }

    function connect() {
      if (
        disposed ||
        !navigator.onLine
      ) {
        return;
      }

      const token = getAuthToken();

      if (!token) {
        scheduleReconnect();
        return;
      }

      const websocketUrl =
        `${WS_BASE}/alerts/` +
        `${encodeURIComponent(
          neighbourhoodId,
        )}/ws` +
        `?token=${encodeURIComponent(token)}`;

      const websocket =
        new WebSocket(websocketUrl);

      websocketRef.current = websocket;

      websocket.onopen = () => {
        if (disposed) {
          return;
        }

        setWsConnected(true);

        // Fetch anything missed during disconnection.
        void reconcile(false);
      };

      websocket.onmessage = (message) => {
        try {
          const event = JSON.parse(
            message.data as string,
          ) as {
            event?: string;
          };

          if (event.event === "ping") {
            return;
          }

          void reconcile(false);
        } catch {
        }
      };

      websocket.onerror = () => {
        websocket.close();
      };

      websocket.onclose = () => {
        if (disposed) {
          return;
        }

        setWsConnected(false);
        scheduleReconnect();
      };
    }

    connect();

    return () => {
      disposed = true;

      if (reconnectTimerRef.current) {
        clearTimeout(
          reconnectTimerRef.current,
        );
      }

      const websocket =
        websocketRef.current;

      if (websocket) {
        websocket.onclose = null;
        websocket.close();
      }

      websocketRef.current = null;
    };
  }, [
    neighbourhoodId,
    isOnline,
    reconcile,
  ]);

  const isStale = usingCachedData || !isOnline || !wsConnected;

  return {
    mappedAlerts,
    unlocatedAlerts,
    lastUpdated,
    loading,
    error,
    isOnline,
    wsConnected,
    isStale,
    usingCachedData,
    refetch: () => reconcile(true),
  };
}
