"use client";

import {
  useEffect,
  useMemo,
} from "react";
import { latLngBounds } from "leaflet";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";

import type {
  AlertRouteData,
  CriticalAlertMapItem,
  CriticalAlertStatus,
} from "@/lib/validators/alert";

import type {
  NeighbourhoodMapProperty,
} from "@/lib/validators/neighbourhood";

import { PropertyLayer } from "./PropertyLayer";

interface CriticalAlertsMapProps {
  readonly alerts: CriticalAlertMapItem[];
  readonly mapProperties: NeighbourhoodMapProperty[];
  readonly showProperties: boolean;
  readonly route: AlertRouteData | null;
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
  CONFIRMED: {
    colour: "#f97316"
  },
  RESOLVED: {
    colour: "#10b981",
  },
  DISMISSED: {
    colour: "#64748b",
    dashArray: "3 5",
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
  if (alerts.some((alert) => alert.status === "OPEN")) {
    return "OPEN";
  }

  if (
    alerts.some(
      (alert) => alert.status === "CONFIRMED",
    )
  ) {
    return "CONFIRMED";
  }

  if (
    alerts.some(
      (alert) => alert.status === "ACKNOWLEDGED",
    )
  ) {
    return "ACKNOWLEDGED";
  }

  if (
    alerts.some(
      (alert) => alert.status === "RESOLVED",
    )
  ) {
    return "RESOLVED";
  }

  return "DISMISSED";
}


function markerRadius(alertCount: number): number {
  return Math.min(10 + alertCount, 18);
}

function FitPropertyBounds({
  properties,
}: {
  readonly properties: readonly {
    latitude: number;
    longitude: number;
  }[];
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

function FitRouteBounds({
  route,
}: {
  readonly route: AlertRouteData | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (!route) {
      return;
    }

    map.fitBounds(
      [
        [
          route.officer_latitude,
          route.officer_longitude,
        ],
        [
          route.property_latitude,
          route.property_longitude,
        ],
      ],
      {
        padding: [60, 60],
        maxZoom: 17,
      },
    );
  }, [map, route]);

  return null;
}


export function CriticalAlertsMap({
  alerts,
  mapProperties,
  showProperties,
  route,
  selectedPropertyId,
  onSelectProperty,
}: CriticalAlertsMapProps) {
  const alertProperties = useMemo(
    () => groupAlertsByProperty(alerts),
    [alerts],
  );

  const geocodedMapProperties = useMemo(
    () =>
      mapProperties.flatMap((property) => {
        if (
          property.latitude === null ||
          property.longitude === null
        ) {
          return [];
        }

        return [
          {
            latitude: property.latitude,
            longitude: property.longitude,
          },
        ];
      }),
    [mapProperties],
  );

  const fitProperties =
    showProperties &&
    geocodedMapProperties.length > 0
      ? geocodedMapProperties
      : alertProperties;

  const displayedPropertyCount =
    showProperties
      ? geocodedMapProperties.length
      : alertProperties.length;

  const routePositions: [number, number][] =
    route?.route_geometry?.coordinates.map(
      ([longitude, latitude]) => [
        latitude,
        longitude,
      ],
    ) ?? [];


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
            {displayedPropertyCount} mapped{" "}
            {displayedPropertyCount === 1
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
          properties={fitProperties}
        />

        <TileLayer
          maxZoom={19}
          attribution={
            '&copy; <a href="https://www.openstreetmap.org/copyright">' +
            "OpenStreetMap contributors"
          }
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitRouteBounds route={route} />

        {routePositions.length > 0 && (
          <Polyline
            positions={routePositions}
            pathOptions={{
              color: "#10b981",
              weight: 5,
              opacity: 0.85,
            }}
          />
        )}

        


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

        {route && (
          <>
            <CircleMarker
              center={[
                route.officer_latitude,
                route.officer_longitude,
              ]}
              radius={9}
              pathOptions={{
                color: "#ffffff",
                fillColor: "#38bdf8",
                fillOpacity: 1,
                weight: 3,
              }}
            >
              <Tooltip direction="top">
                Officer location
              </Tooltip>
            </CircleMarker>

            <CircleMarker
              center={[
                route.property_latitude,
                route.property_longitude,
              ]}
              radius={12}
              pathOptions={{
                color: "#ffffff",
                fillColor: "#ef4444",
                fillOpacity: 0.9,
                weight: 4,
              }}
            >
              <Tooltip direction="top">
                Alert property
              </Tooltip>
            </CircleMarker>
          </>
        )}
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
