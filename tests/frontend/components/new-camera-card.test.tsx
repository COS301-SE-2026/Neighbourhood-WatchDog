import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";

import { NewCameraCard } from "@/components/new-camera-card";
import type { CameraCoverageInput } from "@/lib/validators/camera-coverage";


const TEST_COVERAGE: CameraCoverageInput = {
  origin_latitude: -25.7479,
  origin_longitude: 28.2293,
  coverage_bearing_degrees: 90,
  coverage_angle_degrees: 60,
  coverage_range_metres: 100,
};


jest.mock("@/components/CameraCoverageEditor", () => ({
  CameraCoverageEditor: ({
    propertyLatitude,
    propertyLongitude,
    onChange,
  }: {
    propertyLatitude: number | null;
    propertyLongitude: number | null;
    onChange: (
      value: CameraCoverageInput | undefined,
    ) => void;
  }) => {
    if (
      propertyLatitude === null
      || propertyLongitude === null
    ) {
      return (
        <p>
          This property has no saved map coordinates.
        </p>
      );
    }

    return (
      <button
        type="button"
        onClick={() => onChange(TEST_COVERAGE)}
      >
        Set test POV
      </button>
    );
  },
}));


function fillRequiredFields() {
  fireEvent.change(
    screen.getByLabelText("Camera Name"),
    {
      target: { value: "Front Camera" },
    },
  );

  fireEvent.change(
    screen.getByLabelText("Camera Location"),
    {
      target: { value: "Front Door" },
    },
  );

  fireEvent.change(
    screen.getByLabelText("RTSP URL"),
    {
      target: {
        value: "rtsp://example.com/stream",
      },
    },
  );
}


function renderCard(
  onAcknowledge = jest.fn(),
) {
  render(
    <NewCameraCard
      onClose={jest.fn()}
      onAcknowledge={onAcknowledge}
      propertyLatitude={-25.7479}
      propertyLongitude={28.2293}
    />,
  );

  return onAcknowledge;
}


test("POV option is disabled by default", () => {
  renderCard();

  const checkbox = screen.getByLabelText(
    "Configure camera POV now (optional)",
  );

  expect(checkbox).not.toBeChecked();
  expect(
    screen.queryByText("Set test POV"),
  ).not.toBeInTheDocument();
});


test("camera can be submitted without coverage", () => {
  const onAcknowledge = renderCard();

  fillRequiredFields();

  fireEvent.click(
    screen.getByRole("button", {
      name: "Add camera",
    }),
  );

  expect(onAcknowledge).toHaveBeenCalledWith({
    name: "Front Camera",
    location: "Front Door",
    rtspUrl: "rtsp://example.com/stream",
  });
});


test("enabling POV displays the editor", () => {
  renderCard();

  fireEvent.click(
    screen.getByLabelText(
      "Configure camera POV now (optional)",
    ),
  );

  expect(
    screen.getByRole("button", {
      name: "Set test POV",
    }),
  ).toBeInTheDocument();
});


test("missing property coordinates show a warning", () => {
  render(
    <NewCameraCard
      onClose={jest.fn()}
      onAcknowledge={jest.fn()}
      propertyLatitude={null}
      propertyLongitude={null}
    />,
  );

  fireEvent.click(
    screen.getByLabelText(
      "Configure camera POV now (optional)",
    ),
  );

  expect(
    screen.getByText(
      "This property has no saved map coordinates.",
    ),
  ).toBeInTheDocument();
});


test("incomplete POV prevents camera submission", () => {
  const onAcknowledge = renderCard();

  fillRequiredFields();

  fireEvent.click(
    screen.getByLabelText(
      "Configure camera POV now (optional)",
    ),
  );

  expect(
    screen.getByRole("button", {
      name: "Add camera",
    }),
  ).toBeDisabled();

  expect(onAcknowledge).not.toHaveBeenCalled();
});


test("complete POV is included in the registration data", () => {
  const onAcknowledge = renderCard();

  fillRequiredFields();

  fireEvent.click(
    screen.getByLabelText(
      "Configure camera POV now (optional)",
    ),
  );

  fireEvent.click(
    screen.getByRole("button", {
      name: "Set test POV",
    }),
  );

  fireEvent.click(
    screen.getByRole("button", {
      name: "Add camera",
    }),
  );

  expect(onAcknowledge).toHaveBeenCalledWith({
    name: "Front Camera",
    location: "Front Door",
    rtspUrl: "rtsp://example.com/stream",
    coverage: TEST_COVERAGE,
  });
});


test("disabling POV removes the optional coverage payload", () => {
  const onAcknowledge = renderCard();

  fillRequiredFields();

  const checkbox = screen.getByLabelText(
    "Configure camera POV now (optional)",
  );

  fireEvent.click(checkbox);

  fireEvent.click(
    screen.getByRole("button", {
      name: "Set test POV",
    }),
  );

  fireEvent.click(checkbox);

  fireEvent.click(
    screen.getByRole("button", {
      name: "Add camera",
    }),
  );

  expect(onAcknowledge).toHaveBeenCalledWith({
    name: "Front Camera",
    location: "Front Door",
    rtspUrl: "rtsp://example.com/stream",
  });
});