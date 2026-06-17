import type { Alert } from "@/components/shared/AlertCard";

export const mockAlert: Alert = {
  id: "alert-1",
  camera_id: "cam-1234",
  detection_event_id: "evt-1",
  status: "NEW",
  created_at: new Date().toISOString(),
  detection_type: "HUMAN_PRESENCE",
  confidence_score: 0.85,
  thumbnail_url: null,
};
