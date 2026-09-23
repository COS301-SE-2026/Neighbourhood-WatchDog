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

