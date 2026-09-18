"use client";

import {
  useEffect,
  useMemo,
} from "react";
import { latLngBounds } from "leaflet";
import {
  CircleMarker,
  MapContainer,
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
  readonly selectedPropertyId?: string | null;
  readonly onSelectProperty: (
    property: PropertyAlertGroup,
  ) => void;
}


export interface PropertyAlertGroup {
  propertyId: string;
  propertyAddress: string;
  latitude: number;
  longitude: number;
  alerts: CriticalAlertMapItem[];
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

function groupAlertsByProperty(
  alerts: CriticalAlertMapItem[],
): PropertyAlertGroup[] {
  const properties = new Map<
    string,
    PropertyAlertGroup
  >();

  for (const alert of alerts) {
    const existing = properties.get(
      alert.property_id,
    );

    if (existing) {
      existing.alerts.push(alert);
      continue;
    }

    properties.set(alert.property_id, {
      propertyId: alert.property_id,
      propertyAddress:
        alert.property_address,
      latitude: alert.latitude,
      longitude: alert.longitude,
      alerts: [alert],
    });
  }

  return Array.from(properties.values()).map(
    (property) => ({
      ...property,
      alerts: [...property.alerts].sort(
        (first, second) =>
          new Date(
            second.created_at,
          ).getTime() -
          new Date(
            first.created_at,
          ).getTime(),
      ),
    }),
  );
}

function propertyDetectionType(
  alerts: CriticalAlertMapItem[],
): CriticalAlertMapItem["detection_type"] {
  const hasWeaponAlert = alerts.some(
    (alert) =>
      alert.detection_type ===
      "WEAPON_DETECTED",
  );

  return hasWeaponAlert
    ? "WEAPON_DETECTED"
    : "FALL_DETECTED";
}

function propertyStatus(
  alerts: CriticalAlertMapItem[],
): CriticalAlertStatus {
  const hasOpenAlert = alerts.some(
    (alert) => alert.status === "OPEN",
  );

  if (hasOpenAlert) {
    return "OPEN";
  }

  const hasAcknowledgedAlert = alerts.some(
    (alert) =>
      alert.status === "ACKNOWLEDGED",
  );

  if (hasAcknowledgedAlert) {
    return "ACKNOWLEDGED";
  }

  return "RESOLVED";
}

function markerRadius(alertCount: number): number {
  return Math.min(10 + alertCount, 18);
}

function FitPropertyBounds({
  properties,
}: {
  readonly properties: PropertyAlertGroup[];
}) {
  const map = useMap();

  useEffect(() => {
    if (properties.length === 0) {
      map.setView(DEFAULT_CENTRE, 5);
      return;
    }

    if (properties.length === 1) {
      map.setView(
        [
          properties[0].latitude,
          properties[0].longitude,
        ],
        16,
      );

      return;
    }

    const bounds = latLngBounds(
      properties.map((property) => [
        property.latitude,
        property.longitude,
      ]),
    );

    map.fitBounds(bounds, {
      padding: [40, 40],
      maxZoom: 16,
    });
  }, [map, properties]);

  return null;
}

export function CriticalAlertsMap({
  alerts,
  selectedPropertyId,
  onSelectProperty
}: CriticalAlertsMapProps) {
  const properties = useMemo(
    () => groupAlertsByProperty(alerts),
    [alerts],
  );

  return (
    <section
      aria-label="Critical alert map"
      className="overflow-hidden rounded-lg border border-border bg-brand-depth"
    >
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-brand-frost">
            Neighbourhood map
          </h2>

          <p className="mt-1 text-xs text-brand-ash">
            {properties.length} mapped{" "}
            {properties.length === 1
              ? "property"
              : "properties"}
            {" · "}
            {alerts.length} critical{" "}
            {alerts.length === 1
              ? "alert"
              : "alerts"}
          </p>
        </div>

        <MapLegend />
      </header>

      <MapContainer
        center={DEFAULT_CENTRE}
        zoom={5}
        minZoom={3}
        maxZoom={19}
        scrollWheelZoom
        className="relative z-0 h-[34rem] w-full"
      >
        <FitPropertyBounds
          properties={properties}
        />

        <TileLayer
          maxZoom={19}
          attribution={
            '&copy; <a href="https://www.openstreetmap.org/copyright">' +
            "OpenStreetMap contributors"
          }
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {properties.map((property) => {
          const detectionType =
            propertyDetectionType(
              property.alerts,
            );

          const status = propertyStatus(
            property.alerts,
          );

          const fillColour =
            TYPE_COLOURS[detectionType];

          const statusStyle =
            STATUS_STYLES[status];

          return (
            <CircleMarker
            key={property.propertyId}
            center={[
                property.latitude,
                property.longitude,
            ]}
            radius={markerRadius(
                property.alerts.length,
            )}
            pathOptions={{
                color:
                selectedPropertyId ===
                property.propertyId
                    ? "#ffffff"
                    : statusStyle.colour,
                fillColor: fillColour,
                fillOpacity: 0.85,
                weight:
                selectedPropertyId ===
                property.propertyId
                    ? 6
                    : 4,
                dashArray: statusStyle.dashArray,
            }}
            eventHandlers={{
                click: () =>
                onSelectProperty(property),
            }}
            >
            <Tooltip
                direction="top"
                offset={[0, -8]}
            >
                <div>
                <strong>
                    {property.propertyAddress}
                </strong>

                <br />

                {property.alerts.length} critical{" "}
                {property.alerts.length === 1
                    ? "alert"
                    : "alerts"}
                </div>
            </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </section>
  );
}

function MapLegend() {
  return (
    <div
      aria-label="Map marker legend"
      className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-brand-ash"
    >
      <LegendItem
        colour="#ef4444"
        label="Weapon"
      />

      <LegendItem
        colour="#f59e0b"
        label="Fall"
      />

      <LegendItem
        colour="#ef4444"
        label="Open"
        outline
      />
    </div>
  );
}

function LegendItem({
  colour,
  label,
  outline = false,
}: {
  readonly colour: string;
  readonly label: string;
  readonly outline?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        aria-hidden="true"
        className="size-2.5 rounded-full"
        style={
          outline
            ? {
                border: `2px solid ${colour}`,
                backgroundColor:
                  "transparent",
              }
            : {
                backgroundColor: colour,
              }
        }
      />

      {label}
    </span>
  );
}
