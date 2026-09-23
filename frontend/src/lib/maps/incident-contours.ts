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

function createThresholds(
  minimum: number,
  maximum: number,
  bandCount: number,
): number[] {
  if (maximum <= 0) {
    return [];
  }

  if (minimum === maximum) {
    return [maximum];
  }

  const safeBandCount = Math.min(
    Math.max(bandCount, 2),
    10
  );

  return Array.from(
    {
      length: safeBandCount,
    },
    (_, index) =>
      minimum +
      (
        (
          maximum - minimum
        ) *
        index
      ) /
        (
          safeBandCount - 1
        )
  );
}


function normalizeValue(
  value: number,
  minimum: number,
  maximum: number,
): number {
  if (maximum === minimum) {
    return maximum > 0 ? 1 : 0;
  }

  return Math.min(
    1,
    Math.max(
      0,
      (
        value - minimum
      ) /
        (
          maximum - minimum
        ),
    ),
  );
}

export function buildIncidentContours(
  data: IncidentDensityData,
  bandCount = DEFAULT_BAND_COUNT,
): IncidentContourCollection {
  if (
    data.cells.length === 0 ||
    data.max_count <= 0
  ) {
    return EMPTY_CONTOURS;
  }

  const cellSize = data.cell_size_metres;

  const gridXs = data.cells.map(
    (cell) => cell.grid_x,
  );

  const gridYs = data.cells.map(
    (cell) => cell.grid_y,
  );

  const minimumGridX = Math.min(...gridXs);
  const maximumGridX = Math.max(...gridXs);
  const minimumGridY = Math.min(...gridYs);
  const maximumGridY = Math.max(...gridYs);

  /*
   * One empty-cell border is added around the
   * returned cells. This allows d3-contour to
   * close polygons around edge values.
   */
  const width =
    Math.round(
      (
        maximumGridX - minimumGridX
      ) / cellSize,
    ) + 3;

  const height =
    Math.round(
      (
        maximumGridY - minimumGridY
      ) / cellSize,
    ) + 3;

  if (width <= 0 || height <= 0 || width * height > MAX_RASTER_CELLS) {
    return EMPTY_CONTOURS;
  }

  const values = new Array<number>(
    width * height,
  ).fill(0);

  for (const cell of data.cells) {
    const x =
      Math.round(
        (
          cell.grid_x - minimumGridX
        ) / cellSize,
      ) + 1;

    /*
     * Raster Y increases downwards, whereas
     * Web Mercator Y increases northwards.
     */
    const y =
      Math.round(
        (
          maximumGridY - cell.grid_y
        ) / cellSize,
      ) + 1;

    values[y * width + x] =
      cell.incident_count;
  }

  const thresholds = createThresholds(
    data.min_count,
    data.max_count,
    bandCount,
  );

  const generatedContours = contours()
    .size([
      width,
      height,
    ])
    .thresholds(thresholds)(values);

  const features: Feature<
    MultiPolygon,
    IncidentContourProperties
  >[] = generatedContours.map(
    (generatedContour) => {
      const coordinates =
        generatedContour.coordinates.map(
          (polygon) =>
            polygon.map((ring) =>
              ring.map(
                ([
                  rasterX,
                  rasterY,
                ]) => {
                  const projectedX =
                    minimumGridX +
                    (
                      rasterX - 1
                    ) *
                      cellSize;

                  const projectedY =
                    maximumGridY +
                    (
                      2 - rasterY
                    ) *
                      cellSize;

                  return projectedToLongitudeLatitude(
                    projectedX,
                    projectedY,
                  );
                },
              ),
            ),
        );

      return {
        type: "Feature",
        properties: {
          value: generatedContour.value,
          normalizedValue: normalizeValue(
            generatedContour.value,
            data.min_count,
            data.max_count,
          ),
        },
        geometry: {
          type: "MultiPolygon",
          coordinates,
        },
      };
    },
  );

  /*
   * Lower-value polygons must render first so
   * hotter nested contours remain visible.
   */
  features.sort(
    (first, second) =>
      first.properties.value -
      second.properties.value,
  );

  return {
    type: "FeatureCollection",
    features,
  };
}

