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

const RASTER_PADDING = 1;


const SHAPE_SMOOTHING_ITERATIONS = 3;

type RasterPoint = [
  number,
  number,
];

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

function smoothClosedRing(
  ring: number[][],
  iterations = SHAPE_SMOOTHING_ITERATIONS,
): RasterPoint[] {
  if (ring.length < 4) {
    return ring.map(
      ([x, y]) => [
        x,
        y,
      ],
    );
  }

 
  let points: RasterPoint[] = ring
    .slice(0, -1)
    .map(
      ([x, y]): RasterPoint => [
        x,
        y,
      ],
    );

  if (points.length < 3) {
    return ring.map(
      ([x, y]) => [
        x,
        y,
      ],
    );
  }

  for (
    let iteration = 0;
    iteration < iterations;
    iteration += 1
  ) {
    const nextPoints: RasterPoint[] = [];

    for (
      let index = 0;
      index < points.length;
      index += 1
    ) {
      const current = points[index];

      const next =
        points[
          (
            index + 1
          ) %
            points.length
        ];

      
      nextPoints.push(
        [
          0.75 * current[0] +
            0.25 * next[0],

          0.75 * current[1] +
            0.25 * next[1],
        ],
        [
          0.25 * current[0] +
            0.75 * next[0],

          0.25 * current[1] +
            0.75 * next[1],
        ],
      );
    }

    points = nextPoints;
  }

  const first = points[0];


  return [
    ...points,
    [
      first[0],
      first[1],
    ],
  ];
}

function createThresholds(
  minimum: number,
  maximum: number,
  bandCount: number,
): number[] {
  if (
    maximum <= 0 ||
    maximum < minimum
  ) {
    return [];
  }


  if (maximum === minimum) {
    return [minimum];
  }

  const safeBandCount = Math.min(
    Math.max(bandCount, 2),
    10,
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
        ),
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

  const cellSize =
    data.cell_size_metres;

  const gridXs = data.cells.map(
    (cell) => cell.grid_x,
  );

  const gridYs = data.cells.map(
    (cell) => cell.grid_y,
  );

  const minimumGridX =
    Math.min(...gridXs);

  const maximumGridX =
    Math.max(...gridXs);

  const minimumGridY =
    Math.min(...gridYs);

  const maximumGridY =
    Math.max(...gridYs);

  const horizontalCellCount =
    Math.round(
      (
        maximumGridX -
        minimumGridX
      ) / cellSize,
    ) + 1;

  const verticalCellCount =
    Math.round(
      (
        maximumGridY -
        minimumGridY
      ) / cellSize,
    ) + 1;

  const width =
    horizontalCellCount +
    2 * RASTER_PADDING;

  const height =
    verticalCellCount +
    2 * RASTER_PADDING;

  if (
    width <= 0 ||
    height <= 0 ||
    width * height > MAX_RASTER_CELLS
  ) {
    return EMPTY_CONTOURS;
  }

  const values = new Array<number>(
    width * height,
  ).fill(0);

  for (const cell of data.cells) {
    const x =
      Math.round(
        (
          cell.grid_x -
          minimumGridX
        ) / cellSize,
      ) + RASTER_PADDING;

   
    const y =
      Math.round(
        (
          maximumGridY -
          cell.grid_y
        ) / cellSize,
      ) + RASTER_PADDING;

    values[y * width + x] +=
      cell.incident_count;
  }

  const minimumThreshold = Math.max(
    0.5,
    data.min_count - 0.5,
  );

  const maximumThreshold = Math.max(
    minimumThreshold,
    data.max_count - 0.5,
  );

  const thresholds = createThresholds(
    minimumThreshold,
    maximumThreshold,
    bandCount,
  );

  if (thresholds.length === 0) {
    return EMPTY_CONTOURS;
  }

  const generatedContours = contours()
    .size([
      width,
      height,
    ])
    .thresholds(thresholds)(values);

  const features: Feature<
    MultiPolygon,
    IncidentContourProperties
  >[] = generatedContours
    .filter(
      (generatedContour) =>
        generatedContour.coordinates.length > 0,
    )
    .map(
      (generatedContour) => {
        const coordinates =
          generatedContour.coordinates.map(
            (polygon) =>
              polygon.map((ring) =>
                smoothClosedRing(
                  ring,
                ).map(
                  ([
                    rasterX,
                    rasterY,
                  ]) => {
                    const projectedX =
                      minimumGridX +
                      (
                        rasterX -
                        RASTER_PADDING
                      ) *
                        cellSize;

                    const projectedY =
                      maximumGridY +
                      (
                        RASTER_PADDING +
                        1 -
                        rasterY
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
            value:
              generatedContour.value,

            normalizedValue:
              normalizeValue(
                generatedContour.value,
                minimumThreshold,
                maximumThreshold,
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
   * Draw cooler, larger contours first. Hotter,
   * smaller contours then appear above them.
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
