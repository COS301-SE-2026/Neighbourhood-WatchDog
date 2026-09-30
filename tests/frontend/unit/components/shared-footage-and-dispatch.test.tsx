import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AlertFootagePlayer } from "@/components/shared/AlertFootagePlayer";
import { DispatchRequestPopup, dispatchRouteUrl } from "@/components/shared/DispatchRequestPopup";
import { SequencedFootagePlayer } from "@/components/shared/SequencedFootagePlayer";
import { useClip } from "@/hooks/use-clip";
import { fetchTrackingTimeline } from "@/lib/api/alert";
import { useDispatchNotification } from "@/hooks/use-dispatch";

jest.mock("@/hooks/use-clip", () => ({ useClip: jest.fn() }));
jest.mock("@/lib/api/alert", () => ({ fetchTrackingTimeline: jest.fn() }));
jest.mock("@/hooks/use-dispatch", () => ({ useDispatchNotification: jest.fn() }));
jest.mock("lucide-react", () => new Proxy({}, { get: () => (props: any) => <span {...props} /> }));


const mockUseClip = jest.mocked(useClip);
const mockFetchTrackingTimeline = jest.mocked(fetchTrackingTimeline);
const mockUseDispatch = jest.mocked(useDispatchNotification);


const baseClip = { url: null, status: "idle" as const, errorMessage: null, loadClip: jest.fn() };
const notification = {
  dispatchId: "dispatch-1",
  alertId: "alert-1",
  propertyId: "property-1",
  neighbourhoodId: "neighbourhood-1",
  detectionType: "WEAPON_DETECTED",
  distance: 1500,
  eta: 125,
  notifiedAt: "2026-09-30T08:00:00.000Z",
  expiresAt: null
};


const sightings = [
    {
        id: "sightings-b",
        camera_id: "camera-b",
        camera_name: "Back camera",
        camera_location: "Back gate",
        local_track_id: 2,
        observed_at: "2026-09-30T08:02:00.000Z",
        sequence_no: 2,
        match_confidence: null,
        clip_s3_key: "clip-b",
        clip_expires_at: null,
        latitude: -25.75,
        longitude: 28.23
    },
    {
        id: "sighting-a",
        camera_id: "camera-a",
        camera_name: "Front camera",
        camera_location: "Front gate",
        local_track_id: 1,
        observed_at: "2026-09-30T08:01:00.000Z",
        sequence_no: 1,
        match_confidence: 0.9,
        clip_s3_key: "clip-a",
        clip_expires_at: null,
        latitude: -25.74,
        longitude: 28.22
    }
];


beforeEach(() => {
    jest.clearAllMocks();
    mockUseClip.mockReturnValue(baseClip);
     mockUseDispatch.mockReturnValue({
    notification,
    responding: false,
    outcome: null,
    accept: jest.fn().mockResolvedValue(true),
    decline: jest.fn().mockResolvedValue(true),
  });
});



describe("DispatchRequestPopup", () => {
  test("renders nothing when there is no notification or outcome", () => {
    mockUseDispatch.mockReturnValue({
      notification: null,
      responding: false,
      outcome: null,
      accept: jest.fn(),
      decline: jest.fn()
    });
    const { container } = render(<DispatchRequestPopup neighbourhoodId={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  test("renders a weapon request with distance, ETA, and actions", () => {
    render(<DispatchRequestPopup neighbourhoodId="neighbourhood-1" />);
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(screen.getByText("Weapon detected")).toBeInTheDocument();
    expect(screen.getByText("1.5 km away · ~2 min away")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept dispatch request" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Decline dispatch request" })).toBeEnabled();
  });

  test("renders fallback title, metre distance, short ETA, and disabled buttons", () => {
    mockUseDispatch.mockReturnValue({
      notification: { ...notification, detectionType: "UNKNOWN", distance: 25, eta: 20 },
      responding: true,
      outcome: null,
      accept: jest.fn(),
      decline: jest.fn()
    });
    render(<DispatchRequestPopup neighbourhoodId="n1" />);
    expect(screen.getByText("New dispatch request")).toBeInTheDocument();
    expect(screen.getByText("25 m away · <1 min away")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept dispatch request" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Decline dispatch request" })).toBeDisabled();
  });

  test("renders countdown progress and updates it for an expiring request", () => {
    jest.useFakeTimers();
    const expiresAt = new Date(Date.now() + 60_000).toISOString();
    mockUseDispatch.mockReturnValue({
      notification: { ...notification, expiresAt, distance: null, eta: null },
      responding: false,
      outcome: null,
      accept: jest.fn(),
      decline: jest.fn()
    });
    render(<DispatchRequestPopup neighbourhoodId="n1" />);
    expect(screen.getByText(/1:00|0:59/)).toBeInTheDocument();
    jest.advanceTimersByTime(1000);
    jest.useRealTimers();
  });

  test.each([
    ["ACCEPTED", "Dispatch accepted"],
    ["DECLINED", "Dispatch declined"],
    ["EXPIRED", "Request expired"]
  ] as const)("renders the %s outcome", (outcome, text) => {
    mockUseDispatch.mockReturnValue({
      notification: null,
      responding: false,
      outcome,
      accept: jest.fn(),
      decline: jest.fn()
    });
    render(<DispatchRequestPopup neighbourhoodId="n1" />);
    expect(screen.getByRole("status")).toHaveTextContent(text);
  });

  test("decline delegates to the hook", () => {
    const decline = jest.fn();
    mockUseDispatch.mockReturnValue({ ...mockUseDispatch(), decline });
    render(<DispatchRequestPopup neighbourhoodId="n1" />);
    fireEvent.click(screen.getByRole("button", { name: "Decline dispatch request" }));
    expect(decline).toHaveBeenCalledTimes(1);
  });

  test("logs an error instead of accepting when destination data is missing", async () => {
    const error = jest.spyOn(console, "error").mockImplementation(() => undefined);
    const accept = jest.fn();
    mockUseDispatch.mockReturnValue({
      notification: { ...notification, propertyId: null },
      responding: false,
      outcome: null,
      accept,
      decline: jest.fn()
    });
    render(<DispatchRequestPopup neighbourhoodId="n1" />);
    fireEvent.click(screen.getByRole("button", { name: "Accept dispatch request" }));
    await waitFor(() => expect(error).toHaveBeenCalled());
    expect(accept).not.toHaveBeenCalled();
    error.mockRestore();
  });

  test("encodes route path parameters", () => {
    expect(dispatchRouteUrl("neighbourhood/1", "property/2")).toBe(
      "/dashboard/neighbourhood/neighbourhood%2F1/map?routePropertyId=property%2F2",
    );
  });
});

describe("AlertFootagePlayer", () => {
  test.each([
    ["idle", "Loading footage..."],
    ["loading", "Loading footage..."],
    ["processing", "Footage is being prepared..."],
    ["expired", "The clip has expired"],
    ["forbidden", "You do not have permission to view this footage"],
    ["unavailable", "Clip storage is unavailable."],
    ["error", "Failed to load footage"]
  ] as const)("renders the %s state", (status, text) => {
    mockUseClip.mockReturnValue({ ...baseClip, status });
    render(<AlertFootagePlayer alertId="a1" timestamp="2026-09-30T08:00:00.000Z" />);
    expect(screen.getByText(text)).toBeInTheDocument();
  });

  test("renders a ready video and applies half-speed playback", () => {
    mockUseClip.mockReturnValue({ ...baseClip, status: "ready", url: "https://example.test/clip.mp4" });
    render(<AlertFootagePlayer alertId="a1" timestamp="2026-09-30T08:00:00.000Z" clipKind="tracking-sighting" />);
    const video = screen.getByLabelText(/Detection footage at/);
    expect(video).toHaveAttribute("src", "https://example.test/clip.mp4");
    fireEvent.loadedMetadata(video);
    expect((video as HTMLVideoElement).playbackRate).toBe(0.5);
    expect(mockUseClip).toHaveBeenCalledWith("a1", "tracking-sighting");
  });
});

describe("SequencedFootagePlayer", () => {
  test.each([
    ["idle", "Loading continuous footage..."],
    ["loading", "Loading continuous footage..."],
    ["processing", "Footage is being prepared..."],
    ["expired", "The clip has expired"],
    ["forbidden", "You do not have permission to view this footage"],
    ["unavailable", "Footage unavailable"],
    ["error", "Footage unavailable"]
  ] as const)("renders the %s state", (status, text) => {
    mockUseClip.mockReturnValue({ ...baseClip, status });
    render(<SequencedFootagePlayer alertId="a1" alertTimestamp="2026-09-30T08:00:00.000Z" enabled={false} />);
    expect(screen.getByText(text)).toBeInTheDocument();
  });

  test("sorts supplied sightings, renders the playlist, and advances on ended", () => {
    mockUseClip.mockReturnValue({ ...baseClip, status: "ready", url: "clip.mp4" });
    render(<SequencedFootagePlayer alertId="a1" alertTimestamp="2026-09-30T08:00:00.000Z" enabled sightings={sightings} />);
    expect(screen.getByText(/1 \/ 3/)).toBeInTheDocument();
    expect(screen.getByText(/Origin camera/)).toBeInTheDocument();
    const video = screen.getByLabelText(/Detection footage at/);
    fireEvent.loadedMetadata(video);
    expect((video as HTMLVideoElement).playbackRate).toBe(0.5);
    fireEvent.ended(video);
    expect(screen.getByText(/2 \/ 3/)).toBeInTheDocument();
  });

  test("loads and filters sightings when none are supplied", async () => {
    mockFetchTrackingTimeline.mockResolvedValue({ sightings } as any);
    mockUseClip.mockReturnValue({ ...baseClip, status: "ready", url: "clip.mp4" });
    render(<SequencedFootagePlayer alertId="a1" alertTimestamp="2026-09-30T08:00:00.000Z" enabled />);
    await waitFor(() => expect(mockFetchTrackingTimeline).toHaveBeenCalledWith("a1", expect.any(AbortSignal)));
    await waitFor(() => expect(screen.getByText(/1 \/ 3/)).toBeInTheDocument());
  });

  test("keeps the origin clip when the timeline request fails", async () => {
    mockFetchTrackingTimeline.mockRejectedValue(new Error("not ready"));
    mockUseClip.mockReturnValue({ ...baseClip, status: "ready", url: "clip.mp4" });
    render(<SequencedFootagePlayer alertId="a1" alertTimestamp="2026-09-30T08:00:00.000Z" enabled />);
    await waitFor(() => expect(mockFetchTrackingTimeline).toHaveBeenCalled());
    expect(screen.getByText(/Origin camera/)).toBeInTheDocument();
  });
});