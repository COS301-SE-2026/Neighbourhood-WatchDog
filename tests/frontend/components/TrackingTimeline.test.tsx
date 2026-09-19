import { render, screen, waitFor } from "@testing-library/react";
import { render, screen, waitFor } from "@testing-library/react";
import { ApiError, fetchTrackingTimeline } from "../../../frontend/src/lib/api/alert";
import {
  TrackingTimeline,
} from "../../../frontend/src/components/shared/TrackingTimeline";

jest.mock("@/lib/api/alert", () => {
  const actual = jest.requireActual("../../../frontend/src/lib/api/alert");
  return {
    ...actual,
    fetchTrackingTimeline: jest.fn(),
  };
});

const fetchTrackingTimelineMock = fetchTrackingTimeline as jest.MockedFunction<
  typeof fetchTrackingTimeline
>;

const timeline = {
  alert_id: "alert-1",
  tracking_subject_id: "subject-1",
  alert_status: "OPEN",
  sightings: [
    {
      id: "sighting-1",
      camera_id: "camera-1",
      camera_name: "Front Gate",
      camera_location: "North entrance",
      local_track_id: 17,
      observed_at: "2026-09-18T10:00:00.000Z",
      sequence_no: 2,
      match_confidence: 0.91,
    },
  ],
};

describe("TrackingTimeline", () => {
  beforeEach(() => {
    fetchTrackingTimelineMock.mockReset();
  });

  test("does not fetch when disabled", () => {
    render(
      <TrackingTimeline alertId="alert-1" alertStatus="NEW" enabled={false} />,
    );

    expect(screen.getByText("Tracking timeline")).toBeInTheDocument();
    expect(screen.queryByText("Loading tracking timeline…")).not.toBeInTheDocument();
    expect(fetchTrackingTimelineMock).not.toHaveBeenCalled();
  });

  test("renders loading and then a populated timeline", async () => {
    fetchTrackingTimelineMock.mockResolvedValue(timeline);

    render(
      <TrackingTimeline alertId="alert-1" alertStatus="NEW" enabled />,
    );

    expect(screen.getByText("Loading tracking timeline…")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Front Gate")).toBeInTheDocument();
    });

    expect(screen.getByText("subject-1")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Sequence 2")).toBeInTheDocument();
    expect(screen.getByText("North entrance")).toBeInTheDocument();
    expect(screen.getByText("Local track: 17")).toBeInTheDocument();
    expect(screen.getByText("Match: 91.0%")).toBeInTheDocument();
    expect(fetchTrackingTimelineMock).toHaveBeenCalledWith(
      "alert-1",
      expect.any(AbortSignal),
    );
  });

  test("renders the empty-sightings state after acknowledgement", async () => {
    fetchTrackingTimelineMock.mockResolvedValue({
      ...timeline,
      sightings: [],
    });

    render(
      <TrackingTimeline
        alertId="alert-1"
        alertStatus="ACKNOWLEDGED"
        enabled
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText("No sightings have been recorded yet."),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Terminated after acknowledgement")).toBeInTheDocument();
  });

  test("renders a not-found error", async () => {
    fetchTrackingTimelineMock.mockRejectedValue(
      new ApiError("not found", 404),
    );

    render(
      <TrackingTimeline alertId="alert-1" alertStatus="NEW" enabled />,
    );

    await waitFor(() => {
      expect(
        screen.getByText("No tracking timeline is available for this alert."),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("No tracking timeline is available for this alert.")).toHaveAttribute(
      "class",
      expect.stringContaining("border-brand-caution"),
    );
  });

  test("allows the timeline to be refreshed", async () => {
    fetchTrackingTimelineMock
      .mockResolvedValueOnce({ ...timeline, sightings: [] })
      .mockResolvedValueOnce(timeline);

    const { rerender } = render(
      <TrackingTimeline alertId="alert-1" alertStatus="NEW" enabled refreshKey={0} />,
    );

    await waitFor(() => {
      expect(screen.getByText("No sightings have been recorded yet.")).toBeInTheDocument();
    });

    rerender(
      <TrackingTimeline alertId="alert-1" alertStatus="NEW" enabled refreshKey={1} />,
    );

    await waitFor(() => {
      expect(screen.getByText("Front Gate")).toBeInTheDocument();
    });
    expect(fetchTrackingTimelineMock).toHaveBeenCalledTimes(2);
  });
});
