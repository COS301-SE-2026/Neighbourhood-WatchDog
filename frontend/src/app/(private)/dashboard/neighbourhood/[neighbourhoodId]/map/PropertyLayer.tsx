"use client";

import {
  CircleMarker,
  Tooltip,
} from "react-leaflet";

import type {
  NeighbourhoodMapProperty,
} from "@/lib/validators/neighbourhood";

interface PropertyLayerProps {
  readonly properties: NeighbourhoodMapProperty[];
  readonly visible: boolean;
}

export function PropertyLayer({
  properties,
  visible,
}: PropertyLayerProps) {
  if (!visible) {
    return null;
  }

  return (
    <>
      {properties.map((property) => {
        if (
          property.latitude === null ||
          property.longitude === null
        ) {
          return null;
        }

        return (
          <CircleMarker
            key={property.id}
            center={[
              property.latitude,
              property.longitude,
            ]}
            radius={6}
            pathOptions={{
              color: "#e2e8f0",
              fillColor: "#38bdf8",
              fillOpacity: 0.85,
              weight: 2,
            }}
          >
            <Tooltip direction="top" offset={[0, -6]}>
              <div>
                <strong>
                  {property.address}
                </strong>

                <br />

                <span>
                  {property.property_type.toLowerCase()}
                </span>
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </>
  );
}