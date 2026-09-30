"use client";

import { useEffect, useState } from "react";
import { WS_BASE } from "@/lib/api/alert";
import { getAccessToken, refreshSession } from "@/lib/auth/cognito";

export interface NoCandidateNotification {
  dispatchId: string;
  alertId: string;
  sightingId: string | null;
}

interface SocketMessage {
  event?: string;
  payload?: {
    dispatch_id?: string;
    alert_id?: string;
    triggering_sighting_id?: string | null;
  };
}

export function useNoCandidateDispatch(neighbourhoodId: string | null) {
  const [notification, setNotification] =
    useState<NoCandidateNotification | null>(null);

  useEffect(() => {
    if (!neighbourhoodId) return;

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;
    let attempt = 0;

    const connect = async () => {
      let token: string | null = null;

      try {
        token = getAccessToken() ?? (await refreshSession());
      } catch {
        token = null;
      }

      if (cancelled) return;

      if (!token) {
        reconnectTimer = setTimeout(connect, 3000);
        return;
      }

      const ws = new WebSocket(
        `${WS_BASE}/alerts/${neighbourhoodId}/ws?token=${encodeURIComponent(token)}`,
      );
      socket = ws;

      ws.onopen = () => {
        attempt = 0;
      };

      ws.onmessage = ({ data }) => {
        let message: SocketMessage;

        try {
          message = JSON.parse(data);
        } catch {
          return;
        }

        const payload = message.payload;
        if (
          message.event !== "dispatch.escalated" ||
          !payload?.dispatch_id ||
          !payload.alert_id
        ) {
          return;
        }

        setNotification({
          dispatchId: payload.dispatch_id,
          alertId: payload.alert_id,
          sightingId: payload.triggering_sighting_id ?? null,
        });
      };

      ws.onclose = () => {
        if (socket === ws) socket = null;
        if (cancelled) return;

        const delay = Math.min(1000 * 2 ** attempt, 15000);
        attempt += 1;
        reconnectTimer = setTimeout(connect, delay);
      };
    };

    void connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [neighbourhoodId]);

  return {
    notification,
    dismiss: () => setNotification(null),
  };
}
