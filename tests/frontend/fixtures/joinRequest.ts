import type { JoinRequest } from "@/components/shared/RequestCard";

export const mockJoinRequest: JoinRequest = {
  id: "req-1",
  neighbourhood_id: "n-1",
  user_id: "u-1",
  user_name: "Test User",
  status: "PENDING",
  created_at: new Date().toISOString(),
  resolved_at: null,
};
