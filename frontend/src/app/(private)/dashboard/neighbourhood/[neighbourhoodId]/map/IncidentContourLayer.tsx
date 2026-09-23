"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  GeoJSON,
  Pane,
  useMap,
  useMapEvents,
} from "react-leaflet";

import { useIncidentDensity } from "@/hooks/use-incident-density";
import {
  buildIncidentContours,
  type IncidentContourProperties,
} from "@/lib/maps/incident-contours";
import type {
  IncidentDensityViewport,
} from "@/lib/validators/incident-density";

const CONTOUR_COLOURS = [
  "#2563eb",
  "#06b6d4",
  "#22c55e",
  "#eab308",
  "#f97316",
  "#ef4444",
];

interface IncidentContourLayerProps {
  readonly neighbourhoodId: string;
  readonly startDate: string;
  readonly endDate: string;
  readonly enabled: boolean;
}

function contourColour(
  normalizedValue: number,
): string {
  const index = Math.min(
    CONTOUR_COLOURS.length - 1,
    Math.floor(
      normalizedValue *
        CONTOUR_COLOURS.length,
    ),
  );

  return CONTOUR_COLOURS[index];
}

export function IncidentContourLayer({
  neighbourhoodId,
  startDate,
  endDate,
  enabled,
}: IncidentContourLayerProps) {
  const map = useMap();

  const [
    viewport,
    setViewport,
  ] = useState<
    IncidentDensityViewport | null
  >(null);

  const updateViewport = useCallback(() => {
    const bounds = map.getBounds();

    setViewport({
      west: bounds.getWest(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      north: bounds.getNorth(),
    });
  }, [map]);

  useMapEvents({
    moveend: updateViewport,
    zoomend: updateViewport,
  });

  useEffect(() => {
    updateViewport();
  }, [updateViewport]);

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
        "Unable to render incident contours:",
        error,
      );
    }
  }, [error]);

  const contourGeoJson = useMemo(
    () =>
      data
        ? buildIncidentContours(data)
        : null,
    [data],
  );

  const layerKey = useMemo(() => {
    if (!data || !viewport) {
      return "empty-incident-contours";
    }

    const totalCount = data.cells.reduce(
      (total, cell) =>
        total + cell.incident_count,
      0,
    );

    return [
      data.start_date,
      data.end_date,
      data.cells.length,
      data.max_count,
      totalCount,
      viewport.west.toFixed(5),
      viewport.south.toFixed(5),
      viewport.east.toFixed(5),
      viewport.north.toFixed(5),
    ].join(":");
  }, [
    data,
    viewport,
  ]);

  if (!enabled || !contourGeoJson || contourGeoJson.features.length === 0
  ) {
    return null;
  }

  return (
    <Pane
      name="incident-contours"
      style={{
        zIndex: 300,
        pointerEvents: "none",
      }}
    >
      <GeoJSON
        key={layerKey}
        data={contourGeoJson}
        interactive={false}
        style={(feature) => {
          const properties =
            feature?.properties as
              | IncidentContourProperties
              | undefined;

          const normalizedValue =
            properties?.normalizedValue ?? 0;

          const colour = contourColour(
            normalizedValue,
          );

          return {
            color: colour,
            fillColor: colour,
            fillOpacity: 0.28,
            opacity: 0.85,
            weight: 1.5,
          };
        }}
      />
    </Pane>
  );
}
