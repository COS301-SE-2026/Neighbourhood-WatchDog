import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import {
  AlertCard,
  detectionLabel,
  formatDateTime,
  getSeverity,
  SeverityBadge,
  StatusBadge,
  timeAgo,
  type Alert,
} from "../../../frontend/src/components/shared/AlertCard";

jest.mock("next/dynamic", () => ({
  __esModule: true,
  default: () => () => null,
}));

jest.mock("@/components/shared/AlertFootagePlayer", () => ({
  AlertFootagePlayer: () => null,
}));

jest.mock("@/components/ui/tooltip", () => {
  const React = require("react") as typeof import("react");
  const passthrough = ({ children }: { children: ReactNode }) =>
    React.createElement(React.Fragment, null, children);

  return {
    Tooltip: passthrough,
    TooltipTrigger: passthrough,
    TooltipContent: passthrough,
  };
});

jest.mock("@/components/ui/sheet", () => {
  const React = require("react") as typeof import("react");
  const SheetContext = React.createContext(false);
  const passthrough = ({ children }: { children: ReactNode }) =>
    React.createElement(React.Fragment, null, children);

  const Sheet = ({
    open,
    children,
  }: {
    open?: boolean;
    children: ReactNode;
  }) =>
    React.createElement(
      SheetContext.Provider,
      { value: Boolean(open) },
      children,
    );

  const SheetContent = ({ children }: { children: ReactNode }) =>
    React.useContext(SheetContext)
      ? React.createElement("section", null, children)
      : null;

  const SheetTitle = ({ children }: { children: ReactNode }) =>
    React.createElement("h2", null, children);
  const SheetDescription = ({ children }: { children: ReactNode }) =>
    React.createElement("p", null, children);

  return {
    Sheet,
    SheetContent,
    SheetHeader: passthrough,
    SheetTitle,
    SheetDescription,
  };
});

const makeAlert = (overrides: Partial<Alert> = {}): Alert => ({
  id: "alert-123456",
  camera_id: "camera-abcdef123456",
  frame_timestamp: "2026-09-03T11:59:30.000Z",
  detection_type: "HUMAN_PRESENCE",
  confidence_score: 0.876,
  thumbnail_url: null,
  clip_s3_key: null,
  status: "NEW",
  resolved_by: null,
  resolved_at: null,
  created_at: "2026-09-03T11:59:30.000Z",
  property_address: null,
  property_latitude: null,
  property_longitude: null,
  ...overrides,
});

describe("AlertCard display helpers", () => {
  describe("getSeverity", () => {
    test.each([
      ["WEAPON_DETECTED", "CRITICAL"],
      ["FALL_DETECTED", "CRITICAL"],
      ["LOITERING", "HIGH"],
      ["PERIMETER_SCAN", "HIGH"],
      ["HUMAN_PRESENCE", "MEDIUM"],
      ["UNKNOWN_EVENT", "LOW"],
      [null, "LOW"],
    ])("maps %s to %s", (detectionType, expected) => {
      expect(getSeverity(detectionType)).toBe(expected);
    });
  });

  describe("detectionLabel", () => {
    test.each([
      ["HUMAN_PRESENCE", "Person detected"],
      ["LOITERING", "Loitering detected"],
      ["PERIMETER_SCAN", "Perimeter scanning"],
      ["WEAPON_DETECTED", "Weapon detected"],
      ["FALL_DETECTED", "Fall detected"],
      ["CUSTOM_EVENT", "CUSTOM_EVENT"],
      [null, "Unknown event"],
    ])("formats %s as %s", (detectionType, expected) => {
      expect(detectionLabel(detectionType)).toBe(expected);
    });
  });

  describe("timeAgo", () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date("2026-09-03T12:00:00.000Z"));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    test.each([
      ["2026-09-03T11:59:30.000Z", "30s ago"],
      ["2026-09-03T11:45:00.000Z", "15m ago"],
      ["2026-09-03T09:00:00.000Z", "3h ago"],
    ])("formats recent timestamps", (timestamp, expected) => {
      expect(timeAgo(timestamp)).toBe(expected);
    });

    test("falls back to a formatted date for older timestamps", () => {
      expect(timeAgo("2026-09-01T12:00:00.000Z")).toContain("Sept 2026");
    });
  });

  test("returns the original value when the date is invalid", () => {
    expect(formatDateTime("not-a-date")).toBe("not-a-date");
  });
});

describe("AlertCard rendered states", () => {
  test("renders severity and status badges", () => {
    render(
      createElement(
        "div",
        null,
        createElement(SeverityBadge, { severity: "CRITICAL" }),
        createElement(StatusBadge, { status: "ACKNOWLEDGED" }),
      ),
    );

    expect(screen.getByLabelText("Severity: Critical")).toBeInTheDocument();
    expect(screen.getByLabelText("Status: Acknowledged")).toBeInTheDocument();
  });

  test("renders new-alert actions and invokes their callbacks", async () => {
    const onBroadcast = jest.fn().mockResolvedValue(undefined);
    const onAcknowledge = jest.fn().mockResolvedValue(undefined);

    render(
      createElement(AlertCard, {
        alert: makeAlert(),
        onBroadcast,
        onAcknowledge,
        broadcasting: false,
      }),
    );

    expect(screen.getByRole("article", { name: "Alert: Person detected" })).toBeInTheDocument();
    expect(screen.getByText("88% confidence")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Broadcast alert to the neighbourhood" }),
    );
    await waitFor(() => expect(onBroadcast).toHaveBeenCalledWith("alert-123456"));

    fireEvent.click(screen.getByRole("button", { name: "Acknowledge alert" }));
    await waitFor(() => expect(onAcknowledge).toHaveBeenCalledWith("alert-123456"));
  });

  test("opens details and shows unavailable property information", () => {
    render(
      createElement(AlertCard, {
        alert: makeAlert(),
        broadcasting: false,
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "View alert details" }));

    expect(screen.getByText("Full alert details")).toBeInTheDocument();
    expect(screen.getByText("No thumbnail")).toBeInTheDocument();
    expect(screen.getByText("Property address is unavailable.")).toBeInTheDocument();
    expect(screen.getByText(/Map unavailable because this property has no saved coordinates/)).toBeInTheDocument();
  });

  test("does not show new-alert actions for an acknowledged alert", () => {
    render(
      createElement(AlertCard, {
        alert: makeAlert({ status: "ACKNOWLEDGED" }),
        onBroadcast: jest.fn(),
        onAcknowledge: jest.fn(),
        broadcasting: false,
      }),
    );

    expect(screen.getByLabelText("Status: Acknowledged")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Broadcast alert to the neighbourhood" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Acknowledge alert" })).not.toBeInTheDocument();
  });
});
