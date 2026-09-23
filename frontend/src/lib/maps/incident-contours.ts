import { contours } from "d3-contour";

import type {
  Feature,
  FeatureCollection,
  MultiPolygon,
  Position,
} from "geojson";

import type {
  IncidentDensityData,
} from "@/lib/validators/incident-density";

const WEB_MERCATOR_HALF_WORLD_METRES =
  20037508.34;

const DEFAULT_BAND_COUNT = 6;
const MAX_RASTER_CELLS = 250_000;

export interface IncidentContourProperties {
  value: number;
  normalizedValue: number;
}

export type IncidentContourCollection =
  FeatureCollection<
    MultiPolygon,
    IncidentContourProperties
  >;

const EMPTY_CONTOURS: IncidentContourCollection = {
  type: "FeatureCollection",
  features: [],
};

function projectedToLongitudeLatitude(
  projectedX: number,
  projectedY: number,
): Position {
  const longitude =
    (
      projectedX /
      WEB_MERCATOR_HALF_WORLD_METRES
    ) * 180;

  const mercatorLatitude =
    (
      projectedY /
      WEB_MERCATOR_HALF_WORLD_METRES
    ) * 180;

  const latitude =
    (
      180 /
      Math.PI
    ) *
    (
      2 *
        Math.atan(
          Math.exp(
            (
              mercatorLatitude *
              Math.PI
            ) / 180,
          ),
        ) -
      Math.PI / 2
    );

  return [
    longitude,
    latitude,
  ];
}