import {
  act,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";

import {
  CameraCoverageEditor,
} from "@/components/CameraCoverageEditor";
import type {
  CameraCoverageInput,
} from "@/lib/validators/camera-coverage";


type MapClickHandler = (event: {
  latlng: {
    lat: number;
    lng: number;
  };
}) => void;


let mockMapClick: MapClickHandler | undefined;


jest.mock("react-leaflet", () => ({
  Circle: () => null,
  CircleMarker: () => null,
  Polygon: () => null,
  TileLayer: () => null,
  MapContainer: ({
    children,
  }: {
    children: React.ReactNode;
  }) => (
    <div data-testid="map">
      {children}
    </div>
  ),
  useMapEvents: ({
    click,
  }: {
    click: MapClickHandler;
  }) => {
    mockMapClick = click;
    return null;
  },
}));


const PROPERTY_LATITUDE = -25.7479;
const PROPERTY_LONGITUDE = 28.2293;


function clickMap(
  latitude: number,
  longitude: number,
) {
  expect(mockMapClick).toBeDefined();

  act(() => {
    mockMapClick?.({
      latlng: {
        lat: latitude,
        lng: longitude,
      },
    });
  });
}


function selectCompleteViewingDirection() {
  clickMap(
    PROPERTY_LATITUDE,
    PROPERTY_LONGITUDE,
  );

  clickMap(
    PROPERTY_LATITUDE + 0.0003,
    PROPERTY_LONGITUDE - 0.0003,
  );

  clickMap(
    PROPERTY_LATITUDE - 0.0003,
    PROPERTY_LONGITUDE + 0.0003,
  );
}


function renderEditor(
  onChange = jest.fn(),
) {
  render(
    <CameraCoverageEditor
      propertyLatitude={PROPERTY_LATITUDE}
      propertyLongitude={PROPERTY_LONGITUDE}
      value={undefined}
      onChange={onChange}
    />,
  );

  return onChange;
}


test("missing property coordinates show a warning", () => {
  render(
    <CameraCoverageEditor
      propertyLatitude={null}
      propertyLongitude={null}
      value={undefined}
      onChange={jest.fn()}
    />,
  );

  expect(
    screen.getByText(
      /This property has no saved map coordinates/i,
    ),
  ).toBeInTheDocument();
});


test("origin outside the 100 metre zone is rejected", () => {
  renderEditor();

  clickMap(
    PROPERTY_LATITUDE + 0.002,
    PROPERTY_LONGITUDE,
  );

  expect(
    screen.getByText(
      /camera origin must be within 100 metres/i,
    ),
  ).toBeInTheDocument();
});


test("origin and two viewing edges derive a direction", () => {
  const onChange = renderEditor();

  selectCompleteViewingDirection();

  expect(
    screen.getByText(/Bearing:/),
  ).toBeInTheDocument();

  expect(
    screen.getByText(/Field of view:/),
  ).toBeInTheDocument();

  fireEvent.click(
    screen.getByRole("button", {
      name: "Use this POV",
    }),
  );

  expect(onChange).toHaveBeenCalledWith(
    expect.objectContaining({
      origin_latitude: PROPERTY_LATITUDE,
      origin_longitude: PROPERTY_LONGITUDE,
      coverage_bearing_degrees: expect.any(Number),
      coverage_angle_degrees: expect.any(Number),
      coverage_range_metres: 100,
    }),
  );
});


test("range above 200 metres is rejected", () => {
  renderEditor();

  selectCompleteViewingDirection();

  fireEvent.change(
    screen.getByRole("spinbutton"),
    {
      target: {
        value: "201",
      },
    },
  );

  fireEvent.click(
    screen.getByRole("button", {
      name: "Use this POV",
    }),
  );

  expect(
    screen.getByText(
      "Viewing range must be between 1 and 200 metres.",
    ),
  ).toBeInTheDocument();
});


test("changing range clears previously accepted POV", () => {
  const onChange = renderEditor();

  selectCompleteViewingDirection();

  fireEvent.click(
    screen.getByRole("button", {
      name: "Use this POV",
    }),
  );

  expect(onChange).toHaveBeenLastCalledWith(
    expect.objectContaining({
      coverage_range_metres: 100,
    }),
  );

  fireEvent.change(
    screen.getByRole("spinbutton"),
    {
      target: {
        value: "120",
      },
    },
  );

  expect(onChange).toHaveBeenLastCalledWith(undefined);
});