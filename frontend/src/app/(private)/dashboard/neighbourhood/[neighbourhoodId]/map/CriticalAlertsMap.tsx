"use client";

import Link from "next/link";
import {
  useEffect,
  useMemo,
} from "react";
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

interface PropertyAlertGroup {
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
        className="h-[34rem] w-full"
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
                color: statusStyle.colour,
                fillColor: fillColour,
                fillOpacity: 0.85,
                weight: 4,
                dashArray:
                  statusStyle.dashArray,
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

                  {property.alerts.length}{" "}
                  {property.alerts.length === 1
                    ? "critical alert"
                    : "critical alerts"}
                </div>
              </Tooltip>

              <Popup maxWidth={380}>
                <PropertyAlertPopup
                  property={property}
                />
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </section>
  );
}

function PropertyAlertPopup({
  property,
}: {
  readonly property: PropertyAlertGroup;
}) {
  return (
    <div className="w-72 space-y-3">
      <header>
        <p className="font-semibold text-neutral-900">
          {property.propertyAddress}
        </p>

        <p className="mt-1 text-xs text-neutral-600">
          {property.alerts.length} critical{" "}
          {property.alerts.length === 1
            ? "alert"
            : "alerts"}
        </p>
      </header>

      <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
        {property.alerts.map((alert) => (
          <AlertPopupItem
            key={alert.id}
            alert={alert}
          />
        ))}
      </div>
    </div>
  );
}

function AlertPopupItem({
  alert,
}: {
  readonly alert: CriticalAlertMapItem;
}) {
  const typeColour =
    TYPE_COLOURS[alert.detection_type];

  const statusStyle =
    STATUS_STYLES[alert.status];

  const alertsPageUrl =
    `/dashboard/neighbourhood/` +
    `${alert.neighbourhood_id}/alerts` +
    `?alert=${alert.id}`;

  return (
    <article className="rounded-md border border-neutral-200 bg-white p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <span
            aria-hidden="true"
            className="size-2.5 shrink-0 rounded-full"
            style={{
              backgroundColor: typeColour,
            }}
          />

          <p className="truncate text-xs font-semibold text-neutral-900">
            {detectionLabel(
              alert.detection_type,
            )}
          </p>
        </div>

        <span
          className="shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium"
          style={{
            borderColor:
              statusStyle.colour,
            color: statusStyle.colour,
          }}
        >
          {statusLabel(alert.status)}
        </span>
      </div>

      <dl className="mt-2 space-y-1 text-xs text-neutral-600">
        <div>
          <dt className="inline font-medium text-neutral-800">
            Camera:{" "}
          </dt>

          <dd className="inline">
            {alert.camera_name}
          </dd>
        </div>

        <div>
          <dt className="inline font-medium text-neutral-800">
            Created:{" "}
          </dt>

          <dd className="inline">
            {formatDateTime(
              alert.created_at,
            )}
          </dd>
        </div>
      </dl>

      <Link
        href={alertsPageUrl}
        className="mt-3 inline-flex text-xs font-semibold text-emerald-700 underline-offset-2 hover:underline"
      >
        View alert
      </Link>
    </article>
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
        colour="#38bdf8"
        label="Acknowledged"
        outline
      />

      <LegendItem
        colour="#10b981"
        label="Resolved"
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
