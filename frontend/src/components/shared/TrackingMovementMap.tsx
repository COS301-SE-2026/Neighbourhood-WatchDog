"use client";

import { useEffect } from "react";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  TileLayer,
  useMap,
} from "react-leaflet";

type MovementSighting = {
  id: string;
  observed_at: string;
  latitude: number | null;
  longitude: number | null;
};

interface TrackingMovementMapProps {
  readonly sightings: MovementSighting[];
}

function FitMovementBounds({
  positions,
}: {
  readonly positions: [number, number][];
}) {
  const map = useMap();

  useEffect(() => {
    if (positions.length > 0) {
      map.fitBounds(positions, {
        padding: [24, 24],
      });
    }
  }, [map, positions]);

  return null;
}

export function TrackingMovementMap({
  sightings,
}: TrackingMovementMapProps) {
  const points = sightings.filter(
    (
      sighting,
    ): sighting is MovementSighting & {
      latitude: number;
      longitude: number;
    } =>
      typeof sighting.latitude === "number" &&
      typeof sighting.longitude === "number",
  );

  if (points.length === 0) {
    return (
      <p className="rounded-md border border-border px-3 py-2 text-xs text-brand-ash">
        Movement map is unavailable because camera coordinates were not recorded.
      </p>
    );
  }

  const positions: [number, number][] = points.map((point) => [
    point.latitude,
    point.longitude,
  ]);

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <MapContainer
        center={positions[0]}
        zoom={14}
        className="h-64 w-full"
        scrollWheelZoom={false}
        zoomControl
      >
        <FitMovementBounds positions={positions} />

        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />

        {positions.length > 1 && (
          <Polyline
            positions={positions}
            pathOptions={{
              color: "var(--color-green)",
              weight: 4,
            }}
          />
        )}

        {points.map((point, index) => (
          <CircleMarker
            key={point.id}
            center={positions[index]}
            radius={index === points.length - 1 ? 8 : 6}
            pathOptions={{
              color:
                index === points.length - 1
                  ? "var(--color-pulse)"
                  : "var(--color-green)",
              fillColor:
                index === points.length - 1
                  ? "var(--color-pulse)"
                  : "var(--color-green)",
              fillOpacity: 0.85,
            }}
          />
        ))}
      </MapContainer>
    </div>
  );
}