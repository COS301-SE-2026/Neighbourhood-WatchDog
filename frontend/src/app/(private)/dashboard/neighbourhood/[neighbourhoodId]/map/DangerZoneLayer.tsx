"use client";

import {
  useCallback,
  useMemo,
  useState,
} from "react";

import {
  Pane,
  Rectangle,
  useMap,
  useMapEvents,
} from "react-leaflet";

import { useDangerZones } from "@/hooks/use-danger-zones";

import type {
  DangerZoneViewport,
} from "@/lib/validators/danger-zone";

const DANGER_COLOURS = [
  "#312e81",
  "#6d28d9",
  "#c026d3",
  "#e11d48",
  "#dc2626",
];

interface DangerZoneLayerProps {
  readonly neighbourhoodId: string;
  readonly enabled: boolean;
}

function getViewport(
  map: ReturnType<typeof useMap>,
): DangerZoneViewport {
  const bounds = map.getBounds();

  return {
    west: bounds.getWest(),
    south: bounds.getSouth(),
    east: bounds.getEast(),
    north: bounds.getNorth(),
  };
}

function colourForScore(
  score: number,
): string {
  const safeScore = Math.max(
    0,
    Math.min(1, score),
  );

  const index = Math.min(
    DANGER_COLOURS.length - 1,
    Math.floor(
      safeScore * DANGER_COLOURS.length,
    ),
  );

  return DANGER_COLOURS[index];
}

export function DangerZoneLayer({
  neighbourhoodId,
  enabled,
}: DangerZoneLayerProps) {
  const map = useMap();

  const [viewport, setViewport] =
    useState<DangerZoneViewport>(() =>
      getViewport(map),
    );

  const updateViewport = useCallback(() => {
    setViewport(getViewport(map));
  }, [map]);

  useMapEvents({
    moveend: updateViewport,
    zoomend: updateViewport,
  });

  const {
    data,
    loading,
    error,
  } = useDangerZones({
    neighbourhoodId,
    viewport,
    enabled,
  });

  const validCells = useMemo(
    () =>
      data?.cells.filter((cell) =>
        Number.isFinite(cell.danger_score) &&
        cell.danger_score >= 0 &&
        cell.danger_score <= 1 &&
        cell.south < cell.north &&
        cell.west < cell.east,
      ) ?? [],
    [data],
  );

  if (!enabled) {
    return null;
  }

  return (
    <>
      <Pane
        name="danger-zones"
        style={{
          zIndex: 280,
          pointerEvents: "none",
        }}
      >
        {validCells.map((cell) => {
          const colour =
            colourForScore(
              cell.danger_score,
            );

          return (
            <Rectangle
              key={cell.cell_id}
              bounds={[
                [cell.south, cell.west],
                [cell.north, cell.east],
              ]}
              pathOptions={{
                color: colour,
                fillColor: colour,
                fillOpacity: 0.42,
                opacity: 0.75,
                weight: 0.7,
              }}
            />
          );
        })}
      </Pane>

      <div
        className={
          "pointer-events-none absolute " +
          "left-3 top-3 z-[1000] " +
          "max-w-xs rounded-md border " +
          "border-border bg-brand-depth/95 " +
          "p-3 text-xs shadow-lg"
        }
      >
        {loading && (
          <p role="status">
            Loading danger zones...
          </p>
        )}

        {!loading && error && (
          <p role="alert">
            Unable to load danger zones.
          </p>
        )}

        {!loading &&
          !error &&
          data &&
          validCells.length === 0 && (
            <p>
              No danger-zone data is available
              for this viewport.
            </p>
          )}

        <div
          aria-label="Danger score legend"
          className="mt-2 min-w-44"
        >
          <p className="font-medium">
            Danger score
          </p>

          <div
            className="mt-1 h-2 rounded"
            style={{
              background:
                "linear-gradient(to right, " +
                "#312e81, #6d28d9, #c026d3, " +
                "#e11d48, #dc2626)",
            }}
          />

          <div className="mt-1 flex justify-between">
            <span>
              Low{" "}
              {data?.min_score.toFixed(2) ?? "0.00"}
            </span>

            <span>
              High{" "}
              {data?.max_score.toFixed(2) ?? "0.00"}
            </span>
          </div>
        </div>
      </div>
    </>
  );
}