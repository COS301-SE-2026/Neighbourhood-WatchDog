import {
  render,
  screen,
} from "@testing-library/react";
import type { ReactNode } from "react";

import {
  PropertyLayer,
} from "@/app/(private)/dashboard/neighbourhood/[neighbourhoodId]/map/PropertyLayer";

import type {
  NeighbourhoodMapProperty,
} from "@/lib/validators/neighbourhood";

jest.mock("react-leaflet", () => {
  const React = require("react") as typeof import("react");

  return {
    CircleMarker: ({
      children,
      center,
    }: {
      children: ReactNode;
      center: [number, number];
    }) =>
      React.createElement(
        "div",
        {
          "data-testid": "circle-marker",
          "data-center": center.join(","),
        },
        children,
      ),

    Tooltip: ({
      children,
    }: {
      children: ReactNode;
    }) =>
      React.createElement(
        "div",
        {
          "data-testid": "tooltip",
        },
        children,
      ),
  };
});

const geocodedProperty: NeighbourhoodMapProperty = {
  id: "property-1",
  address: "12 Main Street",
  property_type: "PRIVATE",
  latitude: -25.7479,
  longitude: 28.2293,
};

const ungeocodedProperty: NeighbourhoodMapProperty = {
  id: "property-2",
  address: "Unknown Location",
  property_type: "PUBLIC",
  latitude: null,
  longitude: null,
};

describe("PropertyLayer", () => {
  test("renders nothing when hidden", () => {
    const { container } = render(
      <PropertyLayer
        properties={[geocodedProperty]}
        visible={false}
      />,
    );

    expect(container.firstChild).toBeNull();
  });

  test("renders only geocoded properties", () => {
    render(
      <PropertyLayer
        properties={[
          geocodedProperty,
          ungeocodedProperty,
        ]}
        visible
      />,
    );

    expect(
      screen.getAllByTestId("circle-marker"),
    ).toHaveLength(1);

    expect(
      screen.getByTestId("circle-marker"),
    ).toHaveAttribute(
      "data-center",
      "-25.7479,28.2293",
    );

    expect(
      screen.getByText("12 Main Street"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("private"),
    ).toBeInTheDocument();

    expect(
      screen.queryByText("Unknown Location"),
    ).not.toBeInTheDocument();
  });
});