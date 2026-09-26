"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  Circle,
  Pane,
  useMap,
  useMapEvents,
} from "react-leaflet";

import { useIncidentDensity } from "@/hooks/use-incident-density";

import type {
  IncidentDensityViewport,
} from "@/lib/validators/incident-density";

interface IncidentHeatmapLayerProps {
  readonly neighbourhoodId: string;
  readonly startDate: string;
  readonly endDate: string;
  readonly enabled: boolean;
}

const HEATMAP_COLOURS = [
  "#2563eb",
  "#06b6d4",
  "#22c55e",
  "#eab308",
  "#f97316",
  "#ef4444",
];

function getMapViewport(
  map: ReturnType<typeof useMap>,
): IncidentDensityViewport {
  const bounds = map.getBounds();

  return {
    west: bounds.getWest(),
    south: bounds.getSouth(),
    east: bounds.getEast(),
    north: bounds.getNorth(),
  };
}

function colourForDensity(
  normalizedValue: number,
): string {
  const safeValue = Math.max(
    0,
    Math.min(1, normalizedValue),
  );

  const index = Math.min(
    HEATMAP_COLOURS.length - 1,
    Math.floor(
      safeValue * HEATMAP_COLOURS.length,
    ),
  );

  return HEATMAP_COLOURS[index];
}

export function IncidentHeatmapLayer({
  neighbourhoodId,
  startDate,
  endDate,
  enabled,
}: IncidentHeatmapLayerProps) {
  const map = useMap();

  const [viewport, setViewport] =
    useState<IncidentDensityViewport>(() =>
      getMapViewport(map),
    );

  const updateViewport = useCallback(() => {
    setViewport(getMapViewport(map));
  }, [map]);

  useMapEvents({
    moveend: updateViewport,
    zoomend: updateViewport,
  });

  const {
    data,
    error,
  } = useIncidentDensity({
    neighbourhoodId,
    startDate,
    endDate,
    viewport,
    enabled,
  });

  useEffect(() => {
    if (error) {
      console.error(
        "Unable to render incident heatmap:",
        error,
      );
    }
  }, [error]);

  if (!enabled || !data) {
    return null;
  }

  const maximumCount = Math.max(
    1,
    data.max_count,
  );

  return (
    <Pane
      name="incident-heatmap"
      style={{
        zIndex: 260,
        pointerEvents: "none",
      }}
    >
      {data.cells.map((cell) => {
        const normalizedValue =
          cell.incident_count /
          maximumCount;

        const colour =
          colourForDensity(
            normalizedValue,
          );

        const fillOpacity =
          0.18 +
          normalizedValue * 0.32;

        return (
          <Circle
            key={cell.cell_id}
            center={[
              cell.latitude,
              cell.longitude,
            ]}
            radius={70}
            pathOptions={{
              color: colour,
              fillColor: colour,
              fillOpacity,
              opacity: 0.55,
              weight: 0,
            }}
          />
        );
      })}
    </Pane>
  );
}