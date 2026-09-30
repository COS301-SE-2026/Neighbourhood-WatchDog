import { render, screen } from "@testing-library/react";
import { SituationalBriefPrintTemplate } from "@/components/shared/SituationalBriefPrintTemplate";

jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: React.ImgHTMLAttributes<HTMLImageElement>) => <img {...props} />

}));

const brief = {
  tracking_subject_id: "subject-1",
  generated_at: "2026-09-30T08:00:00.000Z",
  trigger: "WEAPON_DETECTED",
  summary: "Subject moved across the neighbourhood.",
  cameras: [
    { camera_id: "c1", camera_name: "Front camera", camera_location: "Front gate", property_id: "p1" },
    { camera_id: "c2", camera_name: "Back camera", camera_location: "Back gate", property_id: "p2" },
  ],
  alerts: [
    {
      alert_id: "a1", detection_type: "WEAPON_DETECTED", confidence_score: 0.876,
      status: "OPEN", observed_at: "2026-09-30T08:01:00.000Z", camera_id: "c1",
      camera_name: "Front camera", camera_location: "Front gate",
    },
  ],
  sightings: [
    {
      sighting_id: "s1", sequence_no: 1, camera_id: "c1", camera_name: "Front camera",
      camera_location: "Front gate", property_id: "p1", local_track_id: 1,
      observed_at: "2026-09-30T08:02:00.000Z", match_confidence: 0.91,
    },
    {
      sighting_id: "s2", sequence_no: 2, camera_id: "c2", camera_name: "Back camera",
      camera_location: "Back gate", property_id: "p2", local_track_id: 2,
      observed_at: "2026-09-30T08:03:00.000Z", match_confidence: null,
    },
  ],
  last_known_location: {
    camera_id: "c2", camera_name: "Back camera", camera_location: "Back gate",
    property_id: "p2", observed_at: "2026-09-30T08:03:00.000Z",
  },
};

describe("SituationalBriefPrintTemplate", () => {
  test("renders the complete officer report", () => {
    render(<SituationalBriefPrintTemplate brief={brief as any} />);
    expect(screen.getByAltText("Neighbourhood WatchDog logo")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Neighbourhood WatchDog" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Weapon Detected" })).toBeInTheDocument();
    expect(screen.getByText("Subject moved across the neighbourhood.")).toBeInTheDocument();
    expect(screen.getByText("subject-1")).toBeInTheDocument();
    expect(screen.getAllByText("WEAPON_DETECTED").length).toBeGreaterThan(0);
    expect(screen.getByText("87.6%")).toBeInTheDocument();
    expect(screen.getAllByText("Front camera").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Back camera").length).toBeGreaterThan(0);
    expect(screen.getByText("Match confidence: 91.0%")).toBeInTheDocument();
    expect(screen.getAllByText("Officer-only document").length).toBeGreaterThan(0);
  });

  test("renders the generic title and omits primary-alert fields when alerts are empty", () => {
    render(
      <SituationalBriefPrintTemplate
        brief={{ ...brief, generated_at: "invalid-date", alerts: [], sightings: [] } as any}
      />
      
    );
    expect(screen.getByRole("heading", { name: "Situational brief" })).toBeInTheDocument();
    expect(screen.queryByText("Detection type")).not.toBeInTheDocument();
    expect(screen.queryByText("Confidence")).not.toBeInTheDocument();
    expect(screen.queryByText("Observed")).not.toBeInTheDocument();
  });
});