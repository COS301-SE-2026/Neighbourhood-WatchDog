"use client";
import { useEffect, useState, useRef } from "react";

export interface AlertEvent {
  event: string;
  alert_id?: string;
  camera_id?: string;
  detection_type?: string;
  confidence?: number;
}

export function useAlerts(neighbourhoodId: string) {
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(
      `ws://localhost:8000/alerts/${neighbourhoodId}/ws`
    );

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === "ping") return; // ignore keepalive
      setAlerts((prev) => [data, ...prev]);
    };

    wsRef.current = ws;
    return () => ws.close();
  }, [neighbourhoodId]);

  return { alerts, connected };
}