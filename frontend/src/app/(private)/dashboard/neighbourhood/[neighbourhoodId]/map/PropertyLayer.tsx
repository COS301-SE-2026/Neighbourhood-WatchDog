"use client";

import {
  Marker,
  Tooltip,
} from "react-leaflet";

import {
  PROPERTY_MAP_ICON,
} from "@/components/shared/property-map-icon";

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
          <Marker
            key={property.id}
            position={[
              property.latitude,
              property.longitude,
            ]}
            icon={PROPERTY_MAP_ICON}
          >
            <Tooltip direction="top" offset={[0, -36]}>
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
          </Marker>
        );
      })}
    </>
  );
}