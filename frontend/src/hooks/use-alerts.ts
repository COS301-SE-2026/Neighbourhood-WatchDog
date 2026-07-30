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

    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "https://api-staging.neighbourhoodwatchdog.co.za";

    const wsBase = apiUrl.replace(/^http/, "ws");

    const ws = new WebSocket(`${wsBase}/alerts/${neighbourhoodId}/ws`);

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