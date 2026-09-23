import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";

import {
  DateRangePicker,
} from "@/app/(private)/dashboard/neighbourhood/[neighbourhoodId]/map/DateRangePicker";

import {
  MapModeTabs,
} from "@/app/(private)/dashboard/neighbourhood/[neighbourhoodId]/map/MapModeTabs";

import {
  MapLayerControls,
  type MapLayerState,
} from "@/app/(private)/dashboard/neighbourhood/[neighbourhoodId]/map/MapLayerControls";

describe("MapModeTabs", () => {
  test("hides the security tab when unavailable", () => {
    render(
      <MapModeTabs
        mode="neighbourhood"
        securityAvailable={false}
        onChange={jest.fn()}
      />,
    );

    expect(
      screen.getByRole("tab", {
        name: "Neighbourhood",
      }),
    ).toHaveAttribute("aria-selected", "true");

    expect(
      screen.queryByRole("tab", {
        name: "Security",
      }),
    ).not.toBeInTheDocument();
  });

  test("allows an authorised user to select security mode", () => {
    const onChange = jest.fn();

    render(
      <MapModeTabs
        mode="neighbourhood"
        securityAvailable
        onChange={onChange}
      />,
    );

    fireEvent.click(
      screen.getByRole("tab", {
        name: "Security",
      }),
    );

    expect(onChange).toHaveBeenCalledWith(
      "security",
    );
  });

  test("marks security as selected in security mode", () => {
    render(
      <MapModeTabs
        mode="security"
        securityAvailable
        onChange={jest.fn()}
      />,
    );

    expect(
      screen.getByRole("tab", {
        name: "Security",
      }),
    ).toHaveAttribute("aria-selected", "true");
  });
});

describe("MapLayerControls", () => {
  const layers: MapLayerState = {
    properties: true,
    heatmap: false,
    contours: false,
    liveAlerts: true,
    routes: false,
  };

  test("shows neighbourhood layers outside security mode", () => {
    render(
      <MapLayerControls
        layers={layers}
        showSecurityLayers={false}
        canViewRoutes={false}
        onToggle={jest.fn()}
      />,
    );

    expect(
      screen.getByRole("switch", {
        name: /Properties/,
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("switch", {
        name: /Incident heatmap/,
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("switch", {
        name: /Contours/,
      }),
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("switch", {
        name: /Live alerts/,
      }),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByRole("switch", {
        name: /Routes/,
      }),
    ).not.toBeInTheDocument();
  });

  test("shows security layers when authorised", () => {
    render(
      <MapLayerControls
        layers={layers}
        showSecurityLayers
        canViewRoutes
        onToggle={jest.fn()}
      />,
    );

    expect(
      screen.getByRole("switch", {
        name: /Live alerts/,
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("switch", {
        name: /Routes/,
      }),
    ).toBeInTheDocument();
  });

  test("reports the correct toggled layer", () => {
    const onToggle = jest.fn();

    render(
      <MapLayerControls
        layers={layers}
        showSecurityLayers
        canViewRoutes
        onToggle={onToggle}
      />,
    );

    fireEvent.click(
      screen.getByRole("switch", {
        name: /Properties/,
      }),
    );

    fireEvent.click(
      screen.getByRole("switch", {
        name: /Incident heatmap/,
      }),
    );

    fireEvent.click(
      screen.getByRole("switch", {
        name: /Contours/,
      }),
    );

    fireEvent.click(
      screen.getByRole("switch", {
        name: /Live alerts/,
      }),
    );

    fireEvent.click(
      screen.getByRole("switch", {
        name: /Routes/,
      }),
    );

    expect(onToggle.mock.calls).toEqual([
      ["properties"],
      ["heatmap"],
      ["contours"],
      ["liveAlerts"],
      ["routes"],
    ]);
  });

  test("disables routes for users without route permission", () => {
    const onToggle = jest.fn();

    render(
      <MapLayerControls
        layers={layers}
        showSecurityLayers
        canViewRoutes={false}
        onToggle={onToggle}
      />,
    );

    const routes = screen.getByRole("switch", {
      name: /Routes/,
    });

    expect(routes).toBeDisabled();
    expect(routes).toHaveAttribute(
      "aria-disabled",
      "true",
    );

    fireEvent.click(routes);

    expect(onToggle).not.toHaveBeenCalledWith(
      "routes",
    );
  });
});

describe("DateRangePicker", () => {
  test("renders the selected date range", () => {
    render(
      <DateRangePicker
        startDate="2026-08-24"
        endDate="2026-09-23"
        onStartDateChange={jest.fn()}
        onEndDateChange={jest.fn()}
      />,
    );

    expect(
      screen.getByLabelText("Start date", {
        exact: true,
        }),
    ).toHaveValue("2026-08-24");

    expect(
      screen.getByLabelText("End date", {
        exact: true,
        }),
    ).toHaveValue("2026-09-23");

    expect(
      screen.queryByRole("alert"),
    ).not.toBeInTheDocument();
  });

  test("calls the date callbacks", () => {
    const onStartDateChange = jest.fn();
    const onEndDateChange = jest.fn();

    render(
      <DateRangePicker
        startDate="2026-08-24"
        endDate="2026-09-23"
        onStartDateChange={onStartDateChange}
        onEndDateChange={onEndDateChange}
      />,
    );

    fireEvent.change(
      screen.getByLabelText("Start date", {
        exact: true,
        }),
      {
        target: {
          value: "2026-09-01",
        },
      },
    );

    fireEvent.change(
    screen.getByLabelText("End date", {
        exact: true,
        }),
      {
        target: {
          value: "2026-09-20",
        },
      },
    );

    expect(onStartDateChange).toHaveBeenCalledWith(
      "2026-09-01",
    );

    expect(onEndDateChange).toHaveBeenCalledWith(
      "2026-09-20",
    );
  });

  test("shows an error for an invalid date range", () => {
    render(
      <DateRangePicker
        startDate="2026-09-24"
        endDate="2026-09-23"
        onStartDateChange={jest.fn()}
        onEndDateChange={jest.fn()}
      />,
    );

    expect(
      screen.getByRole("alert"),
    ).toHaveTextContent(
      "The start date must be before or equal to the end date.",
    );
  });
});