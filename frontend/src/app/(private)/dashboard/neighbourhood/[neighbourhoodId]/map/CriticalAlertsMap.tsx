"use client";

import { useEffect } from "react";
import { latLngBounds } from "leaflet";
import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";

import type {
  CriticalAlertMapItem,
  CriticalAlertStatus,
} from "@/lib/validators/alert";

interface CriticalAlertsMapProps {
  readonly alerts: CriticalAlertMapItem[];
}

const DEFAULT_CENTRE: [number, number] = [
  -30.5595,
  22.9375,
];

const TYPE_COLOURS: Record<
  CriticalAlertMapItem["detection_type"],
  string
> = {
  WEAPON_DETECTED: "#ef4444",
  FALL_DETECTED: "#f59e0b",
};

const STATUS_STYLES: Record<
  CriticalAlertStatus,
  {
    colour: string;
    dashArray?: string;
  }
> = {
  OPEN: {
    colour: "#ef4444",
  },
  ACKNOWLEDGED: {
    colour: "#38bdf8",
    dashArray: "6 4",
  },
  RESOLVED: {
    colour: "#10b981",
  },
};

function detectionLabel(
  type: CriticalAlertMapItem["detection_type"],
): string {
  switch (type) {
    case "WEAPON_DETECTED":
      return "Weapon detected";
    case "FALL_DETECTED":
      return "Fall detected";
  }
}

function statusLabel(
  status: CriticalAlertStatus,
): string {
  switch (status) {
    case "OPEN":
      return "Open";
    case "ACKNOWLEDGED":
      return "Acknowledged";
    case "RESOLVED":
      return "Resolved";
  }
}

function formatDateTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-ZA", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function FitAlertBounds({
  alerts,
}: CriticalAlertsMapProps) {
  const map = useMap();

  useEffect(() => {
    if (alerts.length === 0) {
      map.setView(DEFAULT_CENTRE, 5);
      return;
    }

    if (alerts.length === 1) {
      map.setView(
        [
          alerts[0].latitude,
          alerts[0].longitude,
        ],
        16,
      );
      return;
    }

    const bounds = latLngBounds(
      alerts.map((alert) => [
        alert.latitude,
        alert.longitude,
      ]),
    );

    map.fitBounds(bounds, {
      padding: [40, 40],
      maxZoom: 16,
    });
  }, [alerts, map]);

  return null;
}
