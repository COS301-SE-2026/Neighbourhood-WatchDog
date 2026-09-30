import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SituationalBrief } from "@/components/shared/SituationalBrief";
import { ApiError, fetchSituationalBrief } from "@/lib/api/alert";

jest.mock("@/lib/api/alert", () => ({
  ApiError: class ApiError extends Error {
    statusCode?: number;
    constructor(message: string, statusCode?: number) {
      super(message);
      this.statusCode = statusCode;
    }
  },
  fetchSituationalBrief: jest.fn(),
}));
jest.mock("@/components/shared/SituationalBriefPrintTemplate", () => ({
  SituationalBriefPrintTemplate: () => <div data-testid="print-template" />
}));
jest.mock("lucide-react", () => new Proxy({}, { get: () => (props: any) => <span {...props} /> }));

const mockFetchBrief = jest.mocked(fetchSituationalBrief);

const brief = {
  tracking_subject_id: "subject-1",
  generated_at: "2026-09-30T08:00:00.000Z",
  trigger: "WEAPON_DETECTED",
  summary: "Subject moved across the neighbourhood.",
  cameras: [
    { 
        camera_id: "c1", 
        camera_name: "Front camera", 
        camera_location: "Front gate", 
        property_id: "p1" 
    },
  ],
  alerts: [
    {
      alert_id: "a1", 
      detection_type: "WEAPON_DETECTED", 
      confidence_score: 0.876,
      status: "OPEN", 
      observed_at: "2026-09-30T08:01:00.000Z", 
      camera_id: "c1",
      camera_name: "Front camera", 
      camera_location: "Front gate"
    },
  ],
  sightings: [
    {
      sighting_id: "s1", 
      sequence_no: 1, 
      camera_id: "c1", 
      camera_name: "Front camera",
      camera_location: "Front gate", 
      property_id: "p1", 
      local_track_id: 1,
      observed_at: "2026-09-30T08:02:00.000Z", 
      match_confidence: 0.91
    },
  ],
  last_known_location: {
    camera_id: "c1", 
    camera_name: "Front camera", 
    camera_location: "Front gate",
    property_id: "p1", 
    observed_at: "2026-09-30T08:03:00.000Z"
  }
};

beforeEach(() => {
  jest.clearAllMocks();
});

describe("SituationalBrief", () => {
  test("does not fetch while disabled", () => {
    render(<SituationalBrief alertId="a1" enabled={false} />);
    expect(mockFetchBrief).not.toHaveBeenCalled();
    expect(screen.getByRole("heading", { name: "Situational brief" })).toBeInTheDocument();
  });

  test("renders a loaded brief and prints it", async () => {
    mockFetchBrief.mockResolvedValue(brief as any);
    const print = jest.spyOn(window, "print").mockImplementation(() => undefined);
    render(<SituationalBrief alertId="a1" enabled refreshKey={1} />);

    expect(screen.getByText("Loading situational brief…")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(brief.summary)).toBeInTheDocument());
    expect(screen.getByText("subject-1")).toBeInTheDocument();
    expect(screen.getByText("WEAPON DETECTED")).toBeInTheDocument();
    expect(screen.getAllByText("Front camera - Front gate")).toHaveLength(2);
    expect(screen.getByText("Cameras visited")).toBeInTheDocument();
    expect(screen.getByText("Associated alerts")).toBeInTheDocument();
    expect(screen.getByText("Sightings")).toBeInTheDocument();
    expect(screen.getByTestId("print-template")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Save as PDF" }));
    expect(print).toHaveBeenCalledTimes(1);
    print.mockRestore();
  });

  test("renders the not-available message for a 404", async () => {
    mockFetchBrief.mockRejectedValue(new ApiError("not found", 404));
    render(<SituationalBrief alertId="a1" enabled />);
    await waitFor(() => expect(screen.getByText("The situational brief is not available yet.")).toBeInTheDocument());
    expect(screen.queryByText("Loading situational brief…")).not.toBeInTheDocument();
  });

  test("renders a regular error message", async () => {
    mockFetchBrief.mockRejectedValue(new Error("service unavailable"));
    render(<SituationalBrief alertId="a1" enabled />);
    await waitFor(() => expect(screen.getByText("service unavailable")).toBeInTheDocument());
  });

  test("renders the fallback error for a non-Error rejection", async () => {
    mockFetchBrief.mockRejectedValue("bad response");
    render(<SituationalBrief alertId="a1" enabled />);
    await waitFor(() => expect(screen.getByText("Failed to load the situational brief.")).toBeInTheDocument());
  });

  test("ignores an abort error", async () => {
    mockFetchBrief.mockRejectedValue(new DOMException("aborted", "AbortError"));
    render(<SituationalBrief alertId="a1" enabled />);
    await waitFor(() => expect(mockFetchBrief).toHaveBeenCalled());
    expect(screen.queryByText("Failed to load the situational brief.")).not.toBeInTheDocument();
  });

  test("falls back to the original value for an invalid date", async () => {
    mockFetchBrief.mockResolvedValue({ ...brief, generated_at: "not-a-date" } as any);
    render(<SituationalBrief alertId="a1" enabled />);
    await waitFor(() => expect(screen.getByText("not-a-date")).toBeInTheDocument());
  });
});