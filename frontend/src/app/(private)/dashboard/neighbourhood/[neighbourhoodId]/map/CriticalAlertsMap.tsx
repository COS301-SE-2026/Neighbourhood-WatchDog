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

export function CriticalAlertsMap({
  alerts,
}: CriticalAlertsMapProps) {
  return (
    <section
      aria-label="Critical alert map"
      className="overflow-hidden rounded-lg border border-border bg-brand-depth"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-brand-frost">
            Neighbourhood map
          </h2>

          <p className="mt-1 text-xs text-brand-ash">
            {alerts.length} mapped{" "}
            {alerts.length === 1 ? "alert" : "alerts"}
          </p>
        </div>

        <MapLegend />
      </div>

      <MapContainer
        center={DEFAULT_CENTRE}
        zoom={5}
        minZoom={3}
        scrollWheelZoom
        className="h-[34rem] w-full"
      >
        <FitAlertBounds alerts={alerts} />

        <TileLayer
          attribution={
            '&copy; <a href="https://www.openstreetmap.org/copyright">' +
            "OpenStreetMap</a> contributors &copy; CARTO"
          }
          url={
            "https://{s}.basemaps.cartocdn.com/" +
            "dark_all/{z}/{x}/{y}{r}.png"
          }
        />

        {alerts.map((alert) => {
          const fillColour =
            TYPE_COLOURS[alert.detection_type];

          const statusStyle =
            STATUS_STYLES[alert.status];

          return (
            <CircleMarker
              key={alert.id}
              center={[
                alert.latitude,
                alert.longitude,
              ]}
              radius={10}
              pathOptions={{
                color: statusStyle.colour,
                fillColor: fillColour,
                fillOpacity: 0.85,
                weight: 4,
                dashArray: statusStyle.dashArray,
              }}
            >
              <Tooltip
                direction="top"
                offset={[0, -8]}
              >
                {detectionLabel(
                  alert.detection_type,
                )}
              </Tooltip>

              <Popup>
                <div className="min-w-56 space-y-3 text-sm">
                  <div>
                    <p className="font-semibold">
                      {detectionLabel(
                        alert.detection_type,
                      )}
                    </p>

                    <p className="text-xs text-neutral-600">
                      {statusLabel(alert.status)}
                    </p>
                  </div>

                  <dl className="space-y-2 text-xs">
                    <div>
                      <dt className="font-medium">
                        Property
                      </dt>
                      <dd>
                        {alert.property_address}
                      </dd>
                    </div>

                    <div>
                      <dt className="font-medium">
                        Camera
                      </dt>
                      <dd>{alert.camera_name}</dd>
                    </div>

                    <div>
                      <dt className="font-medium">
                        Created
                      </dt>
                      <dd>
                        {formatDateTime(
                          alert.created_at,
                        )}
                      </dd>
                    </div>
                  </dl>
                </div>
              </Popup>
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
                backgroundColor: "transparent",
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
