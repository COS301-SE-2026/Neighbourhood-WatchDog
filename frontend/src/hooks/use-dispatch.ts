"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { WS_BASE } from "@/lib/api/alert";
import { getAccessToken, refreshSession } from "@/lib/auth/cognito";
import { respondToDispatch, type DispatchAction } from "@/lib/api/dispatch";

const OUTCOME_DISPLAY_MS = 3000;
const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 15000;

export interface DispatchNotification {
  dispatchId: string;
  alertId: string;
  detectionType: string | null;
  distance: number | null;
  eta: number | null;
  notifiedAt: string;
  expiresAt: string | null;
}

export type DispatchOutcome = "ACCEPTED" | "DECLINED" | "EXPIRED";

interface DispatchSocketEvent {
  event: string;
  payload?: {
    dispatch_id?: string;
    alert_id?: string;
    detection_type?: string;
    distance?: number;
    eta?: number;
    notified_at?: string;
    expires_at?: string;
  };
}

export function useDispatchNotification(neighbourhoodId: string | null) {
  const [notification, setNotification] = useState<DispatchNotification | null>(
    null,
  );
  const [responding, setResponding] = useState(false);
  const [outcome, setOutcome] = useState<DispatchOutcome | null>(null);

  const expiryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const outcomeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearExpiryTimer = useCallback(() => {
    if (!expiryTimer.current) return;

    clearTimeout(expiryTimer.current);
    expiryTimer.current = null;
  }, []);

  const showOutcome = useCallback(
    (status: DispatchOutcome) => {
      clearExpiryTimer();

      setNotification(null);
      setOutcome(status);

      if (outcomeTimer.current) {
        clearTimeout(outcomeTimer.current);
      }

      outcomeTimer.current = setTimeout(() => {
        setOutcome(null);
      }, OUTCOME_DISPLAY_MS);
    },
    [clearExpiryTimer],
  );

  useEffect(() => {
    if (!neighbourhoodId) {
      return;
    }

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;
    let cancelled = false;

    const handleMessage = ({ data }: MessageEvent) => {
      let message: DispatchSocketEvent;

      try {
        message = JSON.parse(data);
      } catch {
        return;
      }

      if (
        message.event !== "dispatch.notified" ||
        !message.payload?.dispatch_id
      ) {
        return;
      }

      const {
        dispatch_id,
        alert_id,
        detection_type,
        distance,
        eta,
        notified_at,
        expires_at,
      } = message.payload;

      clearExpiryTimer();
      setOutcome(null);

      setNotification({
        dispatchId: dispatch_id,
        alertId: alert_id ?? "",
        detectionType: detection_type ?? null,
        distance: distance ?? null,
        eta: eta ?? null,
        notifiedAt: notified_at ?? new Date().toISOString(),
        expiresAt: expires_at ?? null,
      });
    };

    const scheduleReconnect = () => {
      if (cancelled) return;

      const delay = Math.min(
        RECONNECT_BASE_MS * 2 ** attempt,
        RECONNECT_MAX_MS,
      );
      attempt += 1;
      reconnectTimer = setTimeout(connect, delay);
    };

    const connect = async () => {
      if (cancelled) return;

      let token: string | null = null;

      try {
        // Access token lives in memory and expires; refresh if it's gone.
        token = getAccessToken() ?? (await refreshSession());
      } catch {
        token = null;
      }

      if (cancelled) return;

      if (!token) {
        scheduleReconnect();
        return;
      }

      const ws = new WebSocket(
        `${WS_BASE}/alerts/${neighbourhoodId}/ws?token=${encodeURIComponent(token)}`,
      );
      socket = ws;

      ws.onopen = () => {
        attempt = 0;
      };
      ws.onmessage = handleMessage;
      ws.onclose = () => {
        if (socket === ws) socket = null;
        scheduleReconnect();
      };
    };

    void connect();

    return () => {
      cancelled = true;

      if (reconnectTimer) clearTimeout(reconnectTimer);

      const ws = socket;
      socket = null;
      ws?.close();

      clearExpiryTimer();

      if (outcomeTimer.current) {
        clearTimeout(outcomeTimer.current);
      }
    };
  }, [neighbourhoodId, clearExpiryTimer]);

  useEffect(() => {
    clearExpiryTimer();

    if (!notification?.expiresAt) {
      return;
    }

    const millisecondsRemaining =
      new Date(notification.expiresAt).getTime() - Date.now();

    if (millisecondsRemaining <= 0) {
      queueMicrotask(() => showOutcome("EXPIRED"));
      return;
    }

    expiryTimer.current = setTimeout(() => {
      showOutcome("EXPIRED");
    }, millisecondsRemaining);
  }, [
    notification?.dispatchId,
    notification?.expiresAt,
    clearExpiryTimer,
    showOutcome,
  ]);

  const respond = useCallback(
    async (action: DispatchAction) => {
      if (!notification || responding) {
        return;
      }

      setResponding(true);

      try {
        await respondToDispatch(notification.dispatchId, action);

        showOutcome(action === "ACCEPT" ? "ACCEPTED" : "DECLINED");
      } catch {
        showOutcome("EXPIRED");
      } finally {
        setResponding(false);
      }
    },
    [notification, responding, showOutcome],
  );

  return {
    notification,
    responding,
    outcome,
    accept: () => respond("ACCEPT"),
    decline: () => respond("DECLINE"),
  };
}
