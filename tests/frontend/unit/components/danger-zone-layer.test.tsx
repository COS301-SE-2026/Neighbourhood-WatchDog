import type {
  ReactNode,
} from "react";

import {
  render,
  screen,
} from "@testing-library/react";

import {
  DangerZoneLayer,
} from "@/app/(private)/dashboard/neighbourhood/[neighbourhoodId]/map/DangerZoneLayer";

import {
  useDangerZones,
} from "@/hooks/use-danger-zones";

import type {
  DangerZoneData,
} from "@/lib/validators/danger-zone";

jest.mock("@/hooks/use-danger-zones", () => ({
  useDangerZones: jest.fn(),
}));

jest.mock("react-leaflet", () => {
  const React =
    require("react") as typeof import("react");

  return {
    Pane: ({
      children,
    }: {
      children: ReactNode;
    }) =>
      React.createElement(
        "div",
        {
          "data-testid": "danger-pane",
        },
        children,
      ),

    Rectangle: ({
      bounds,
    }: {
      bounds: [
        [number, number],
        [number, number],
      ];
    }) =>
      React.createElement("div", {
        "data-testid": "danger-rectangle",
        "data-bounds": JSON.stringify(bounds),
      }),

    useMap: () => ({
      getBounds: () => ({
        getWest: () => 28.20,
        getSouth: () => -25.80,
        getEast: () => 28.30,
        getNorth: () => -25.70,
      }),
    }),

    useMapEvents: jest.fn(),
  };
});

const mockedUseDangerZones =
  jest.mocked(useDangerZones);

const baseData: DangerZoneData = {
  neighbourhood_id:
    "00000000-0000-0000-0000-000000000001",
  window_start: "2026-08-27",
  window_end: "2026-09-25",
  calculated_at:
    "2026-09-25T14:00:00Z",
  cell_size_metres: 100,
  min_score: 0.15,
  max_score: 0.90,
  cells: [
    {
      cell_id: "valid-cell",
      grid_x: 3142700,
      grid_y: -2963800,
      latitude: -25.75,
      longitude: 28.23,
      south: -25.7504,
      west: 28.2295,
      north: -25.7496,
      east: 28.2305,
      incident_count: 10,
      incident_score: 1,
      coverage_ratio: 0.1,
      coverage_sparsity: 0.9,
      danger_score: 0.9,
    },
  ],
};

describe("DangerZoneLayer", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders nothing while disabled", () => {
    mockedUseDangerZones.mockReturnValue({
      data: baseData,
      loading: false,
      error: null,
    });

    const { container } = render(
      <DangerZoneLayer
        neighbourhoodId="neighbourhood-1"
        enabled={false}
      />,
    );

    expect(container.firstChild).toBeNull();
    expect(
      mockedUseDangerZones,
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        enabled: false,
      }),
    );
  });

  test("renders valid danger cells as rectangles", () => {
    mockedUseDangerZones.mockReturnValue({
      data: baseData,
      loading: false,
      error: null,
    });

    render(
      <DangerZoneLayer
        neighbourhoodId="neighbourhood-1"
        enabled
      />,
    );

    expect(
      screen.getAllByTestId("danger-rectangle"),
    ).toHaveLength(1);

    expect(
      screen.getByTestId("danger-rectangle"),
    ).toHaveAttribute(
      "data-bounds",
      JSON.stringify([
        [-25.7504, 28.2295],
        [-25.7496, 28.2305],
      ]),
    );

    expect(
      screen.getByLabelText("Danger score legend"),
    ).toBeInTheDocument();
  });

  test("filters invalid danger scores and invalid bounds", () => {
    mockedUseDangerZones.mockReturnValue({
      data: {
        ...baseData,
        cells: [
          ...baseData.cells,
          {
            ...baseData.cells[0],
            cell_id: "invalid-score",
            danger_score: 1.5,
          },
          {
            ...baseData.cells[0],
            cell_id: "invalid-bounds",
            south: -25.70,
            north: -25.80,
          },
        ],
      },
      loading: false,
      error: null,
    });

    render(
      <DangerZoneLayer
        neighbourhoodId="neighbourhood-1"
        enabled
      />,
    );

    expect(
      screen.getAllByTestId("danger-rectangle"),
    ).toHaveLength(1);
  });

  test("shows loading state", () => {
    mockedUseDangerZones.mockReturnValue({
      data: null,
      loading: true,
      error: null,
    });

    render(
      <DangerZoneLayer
        neighbourhoodId="neighbourhood-1"
        enabled
      />,
    );

    expect(
      screen.getByRole("status"),
    ).toHaveTextContent(
      "Loading danger zones",
    );
  });

  test("shows empty state", () => {
    mockedUseDangerZones.mockReturnValue({
      data: {
        ...baseData,
        cells: [],
        min_score: 0,
        max_score: 0,
      },
      loading: false,
      error: null,
    });

    render(
      <DangerZoneLayer
        neighbourhoodId="neighbourhood-1"
        enabled
      />,
    );

    expect(
      screen.getByText(
        "No danger-zone data is available for this viewport.",
      ),
    ).toBeInTheDocument();
  });

  test("shows error state", () => {
    mockedUseDangerZones.mockReturnValue({
      data: null,
      loading: false,
      error: "Request failed",
    });

    render(
      <DangerZoneLayer
        neighbourhoodId="neighbourhood-1"
        enabled
      />,
    );

    expect(
      screen.getByRole("alert"),
    ).toHaveTextContent(
      "Unable to load danger zones.",
    );
  });
});