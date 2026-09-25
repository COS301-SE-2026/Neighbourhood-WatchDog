"use client";

import { useMemo, useState } from "react";
import {
  Circle,
  CircleMarker,
  MapContainer,
  Polygon,
  TileLayer,
  useMapEvents,
} from "react-leaflet";

import {
  cameraCoverageSchema,
  MAX_CAMERA_COVERAGE_RANGE_METRES,
  MAX_CAMERA_ORIGIN_DISTANCE_METRES,
  type CameraCoverageInput,
} from "@/lib/validators/camera-coverage";

const EARTH_RADIUS_METRES = 6_371_000;
const SECTOR_ARC_SEGMENTS = 24;

type Coordinate = [number, number];

type CameraCoverageEditorProps = {
  propertyLatitude: number | null;
  propertyLongitude: number | null;
  value: CameraCoverageInput | undefined;
  onChange: (value: CameraCoverageInput | undefined) => void;
};

function toRadians(value: number): number {
  return (value * Math.PI) / 180;
}

function toDegrees(value: number): number {
  return (value * 180) / Math.PI;
}

function distanceMetres(first: Coordinate, second: Coordinate): number {
  const firstLatitude = toRadians(first[0]);
  const secondLatitude = toRadians(second[0]);
  const latitudeDelta = toRadians(second[0] - first[0]);
  const longitudeDelta = toRadians(second[1] - first[1]);

  const a =
    Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(firstLatitude) *
      Math.cos(secondLatitude) *
      Math.sin(longitudeDelta / 2) ** 2;

  return (
    2 *
    EARTH_RADIUS_METRES *
    Math.asin(Math.min(1, Math.sqrt(a)))
  );
}

function bearingDegrees(from: Coordinate, to: Coordinate): number {
  const fromLatitude = toRadians(from[0]);
  const toLatitude = toRadians(to[0]);
  const longitudeDelta = toRadians(to[1] - from[1]);

  const y = Math.sin(longitudeDelta) * Math.cos(toLatitude);
  const x =
    Math.cos(fromLatitude) * Math.sin(toLatitude) -
    Math.sin(fromLatitude) *
      Math.cos(toLatitude) *
      Math.cos(longitudeDelta);

  return (toDegrees(Math.atan2(y, x)) + 360) % 360;
}

function destinationPoint(
  origin: Coordinate,
  bearing: number,
  rangeMetres: number,
): Coordinate {
  const latitude = toRadians(origin[0]);
  const longitude = toRadians(origin[1]);
  const bearingRadians = toRadians(bearing);
  const angularDistance = rangeMetres / EARTH_RADIUS_METRES;

  const destinationLatitude = Math.asin(
    Math.sin(latitude) * Math.cos(angularDistance) +
      Math.cos(latitude) *
        Math.sin(angularDistance) *
        Math.cos(bearingRadians),
  );

  const destinationLongitude =
    longitude +
    Math.atan2(
      Math.sin(bearingRadians) *
        Math.sin(angularDistance) *
        Math.cos(latitude),
      Math.cos(angularDistance) -
        Math.sin(latitude) *
          Math.sin(destinationLatitude),
    );

  return [
    toDegrees(destinationLatitude),
    ((toDegrees(destinationLongitude) + 540) % 360) - 180,
  ];
}

function deriveBearingAndAngle(
  origin: Coordinate,
  leftEdge: Coordinate,
  rightEdge: Coordinate,
): Pick<
  CameraCoverageInput,
  "coverage_bearing_degrees" | "coverage_angle_degrees"
> {
  const leftBearing = bearingDegrees(origin, leftEdge);
  const rightBearing = bearingDegrees(origin, rightEdge);
  const clockwiseDifference = (rightBearing - leftBearing + 360) % 360;

  if (clockwiseDifference <= 180) {
    return {
      coverage_bearing_degrees:
        (leftBearing + clockwiseDifference / 2) % 360,
      coverage_angle_degrees: clockwiseDifference,
    };
  }

  const counterClockwiseDifference = 360 - clockwiseDifference;

  return {
    coverage_bearing_degrees:
      (rightBearing + counterClockwiseDifference / 2) % 360,
    coverage_angle_degrees: counterClockwiseDifference,
  };
}

function MapClickHandler({
  property,
  origin,
  leftEdge,
  rightEdge,
  onSelectOrigin,
  onSelectLeftEdge,
  onSelectRightEdge,
  onInvalidOrigin,
}: {
  property: Coordinate;
  origin: Coordinate | undefined;
  leftEdge: Coordinate | undefined;
  rightEdge: Coordinate | undefined;
  onSelectOrigin: (coordinate: Coordinate) => void;
  onSelectLeftEdge: (coordinate: Coordinate) => void;
  onSelectRightEdge: (coordinate: Coordinate) => void;
  onInvalidOrigin: () => void;
}) {
  useMapEvents({
    click(event) {
      const coordinate: Coordinate = [
        event.latlng.lat,
        event.latlng.lng,
      ];

      if (!origin) {
        if (distanceMetres(property, coordinate) > MAX_CAMERA_ORIGIN_DISTANCE_METRES) {
          onInvalidOrigin();
          return;
        }

        onSelectOrigin(coordinate);
        return;
      }

      if (!leftEdge) {
        onSelectLeftEdge(coordinate);
        return;
      }

      if (!rightEdge) {
        onSelectRightEdge(coordinate);
      }
    },
  });

  return null;
}

export function CameraCoverageEditor({
  propertyLatitude,
  propertyLongitude,
  value,
  onChange,
}: CameraCoverageEditorProps) {
  const property = useMemo<Coordinate | null>(() => {
    if (propertyLatitude === null || propertyLongitude === null) {
      return null;
    }

    return [propertyLatitude, propertyLongitude];
  }, [propertyLatitude, propertyLongitude]);

  const [origin, setOrigin] = useState<Coordinate | undefined>(
    value
      ? [value.origin_latitude, value.origin_longitude]
      : undefined,
  );
  const [leftEdge, setLeftEdge] = useState<Coordinate | undefined>();
  const [rightEdge, setRightEdge] = useState<Coordinate | undefined>();
  const [rangeMetres, setRangeMetres] = useState(
    value?.coverage_range_metres ?? 100,
  );
  const [message, setMessage] = useState<string | null>(null);

  const derivedDirection = useMemo(() => {
    if (!origin || !leftEdge || !rightEdge) {
      return null;
    }

    return deriveBearingAndAngle(origin, leftEdge, rightEdge);
  }, [origin, leftEdge, rightEdge]);

  const previewPolygon = useMemo(() => {
    if (!origin || !derivedDirection || rangeMetres < 1) {
      return null;
    }

    const startBearing =
      derivedDirection.coverage_bearing_degrees -
      derivedDirection.coverage_angle_degrees / 2;

    const arcPoints = Array.from(
      { length: SECTOR_ARC_SEGMENTS + 1 },
      (_, index): Coordinate =>
        destinationPoint(
          origin,
          startBearing +
            (derivedDirection.coverage_angle_degrees * index) /
              SECTOR_ARC_SEGMENTS,
          rangeMetres,
        ),
    );

    return [
      origin,
      ...arcPoints,
      origin,
    ] satisfies Coordinate[];
    }, [origin, derivedDirection, rangeMetres]);


  if (!property) {
    return (
      <div className="rounded-md border border-brand-caution/40 bg-brand-caution/10 p-3 text-sm text-brand-caution">
        This property has no saved map coordinates. Add the property coordinates before configuring a camera POV.
      </div>
    );
  }

  const completeCoverage = () => {
    if (!origin || !derivedDirection) {
      setMessage("Select the camera origin, then the left and right viewing edges.");
      return;
    }

    const result = cameraCoverageSchema.safeParse({
      origin_latitude: origin[0],
      origin_longitude: origin[1],
      ...derivedDirection,
      coverage_range_metres: rangeMetres,
    });

    if (!result.success) {
      setMessage(`Viewing range must be between 1 and ${MAX_CAMERA_COVERAGE_RANGE_METRES} metres.`);
      return;
    }

    setMessage(null);
    onChange(result.data);
  };

  const reset = () => {
    setOrigin(undefined);
    setLeftEdge(undefined);
    setRightEdge(undefined);
    setMessage(null);
    onChange(undefined);
  };

  const instruction = !origin
    ? "Click inside the dashed circle to place the camera."
    : !leftEdge
      ? "Now click the left edge of the camera view."
      : !rightEdge
        ? "Now click the right edge of the camera view."
        : "POV preview ready. Adjust the range or reset the points.";

  return (
    <div className="space-y-3 rounded-lg border border-border bg-brand-abyss p-3">
      <div>
        <p className="text-sm font-medium text-brand-frost">
          Camera POV (optional)
        </p>
        <p className="mt-1 text-xs text-brand-ash">
          {instruction} The camera origin must remain within {MAX_CAMERA_ORIGIN_DISTANCE_METRES} metres of the property marker.
        </p>
      </div>

      <div className="overflow-hidden rounded-md border border-border">
        <MapContainer
          center={property}
          zoom={17}
          scrollWheelZoom
          className="h-72 w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />
          <MapClickHandler
            property={property}
            origin={origin}
            leftEdge={leftEdge}
            rightEdge={rightEdge}
            onSelectOrigin={(coordinate) => {
              setOrigin(coordinate);
              setMessage(null);
            }}
            onSelectLeftEdge={(coordinate) => {
              setLeftEdge(coordinate);
              setMessage(null);
            }}
            onSelectRightEdge={(coordinate) => {
              setRightEdge(coordinate);
              setMessage(null);
            }}
            onInvalidOrigin={() => {
              setMessage(
                `The camera origin must be within ${MAX_CAMERA_ORIGIN_DISTANCE_METRES} metres of the property.`,
              );
            }}
          />
          <Circle
            center={property}
            radius={MAX_CAMERA_ORIGIN_DISTANCE_METRES}
            pathOptions={{
              color: "#f59e0b",
              dashArray: "6 6",
              fillColor: "#f59e0b",
              fillOpacity: 0.08,
            }}
          />
          <CircleMarker
            center={property}
            radius={7}
            pathOptions={{
              color: "#e2e8f0",
              fillColor: "#38bdf8",
              fillOpacity: 0.9,
            }}
          />
          {origin && (
            <CircleMarker
              center={origin}
              radius={7}
              pathOptions={{
                color: "#e2e8f0",
                fillColor: "#22c55e",
                fillOpacity: 0.95,
              }}
            />
          )}
          {leftEdge && (
            <CircleMarker
              center={leftEdge}
              radius={5}
              pathOptions={{ color: "#f97316", fillColor: "#f97316" }}
            />
          )}
          {rightEdge && (
            <CircleMarker
              center={rightEdge}
              radius={5}
              pathOptions={{ color: "#f97316", fillColor: "#f97316" }}
            />
          )}
          {previewPolygon && (
            <Polygon
              positions={previewPolygon}
              pathOptions={{
                color: "#22c55e",
                fillColor: "#22c55e",
                fillOpacity: 0.24,
              }}
            />
          )}
        </MapContainer>
      </div>

      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium text-brand-frost">
          Viewing range (metres)
        </span>
        <input
          type="number"
          min={1}
          max={MAX_CAMERA_COVERAGE_RANGE_METRES}
          step={1}
          value={rangeMetres}
          onChange={(event) => {
                const nextValue = Number(event.target.value);

                setRangeMetres(
                    Number.isFinite(nextValue)
                        ? nextValue
                        : 0,
                    );

                setMessage(null);
                onChange(undefined);
            }}
          className="h-9 rounded-md border border-border bg-mist/10 px-3 text-brand-frost"
        />
        <span className="text-xs text-brand-ash">
          Maximum allowed range: {MAX_CAMERA_COVERAGE_RANGE_METRES} metres.
        </span>
      </label>

      {derivedDirection && (
        <div className="grid grid-cols-2 gap-2 text-xs text-brand-ash">
          <span>
            Bearing: {derivedDirection.coverage_bearing_degrees.toFixed(1)}°
          </span>
          <span>
            Field of view: {derivedDirection.coverage_angle_degrees.toFixed(1)}°
          </span>
        </div>
      )}

      {message && <p className="text-xs text-threat">{message}</p>}

      <div className="flex gap-2">
        <button
          type="button"
          onClick={completeCoverage}
          disabled={!origin || !leftEdge || !rightEdge}
          className="rounded-md bg-brand-green px-3 py-2 text-xs font-medium text-brand-void disabled:cursor-not-allowed disabled:opacity-50"
        >
          Use this POV
        </button>
        <button
          type="button"
          onClick={reset}
          className="rounded-md border border-border px-3 py-2 text-xs font-medium text-brand-frost"
        >
          Reset map points
        </button>
      </div>
    </div>
  );
}