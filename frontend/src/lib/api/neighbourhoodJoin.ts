import type {
  JoinRequest,
  JoinRequestStatus,
} from "@/components/shared/RequestCard";
import { getApiBaseUrl, getAuthHeaders } from "@/lib/api/auth";

const API_BASE = getApiBaseUrl();

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Type for the API response (without user_name)
type JoinRequestApiResponse = {
  id: string;
  neighbourhood_id: string;
  user_id: string;
  status: JoinRequestStatus;
  created_at: string;
  resolved_at?: string | null;
};

// Fetch user details by ID
async function fetchUser(
  userId: string,
): Promise<{ first_name: string; last_name: string; email: string } | null> {
  try {
    const res = await fetch(`${API_BASE}/users/${userId}`, {
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      console.warn("Failed to load user for join request", {
        userId,
        status: res.status,
        response: text,
      });
      return null;
    }

    return await res.json();
  } catch (error) {
    console.warn("Network error loading user for join request", {
      userId,
      error,
    });
    return null;
  }
}

// Generate display name from user data
function getDisplayName(
  user: { first_name: string; last_name: string; email: string } | null,
): string {
  if (!user) return "Unknown User";

  const fullName = `${user.first_name || ""} ${user.last_name || ""}`.trim();
  return fullName || user.email || "Unknown User";
}

export async function submitJoinRequest(
  joinCode: string,
): Promise<JoinRequest> {
  const res = await fetch(`${API_BASE}/neighbourhood/join`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ join_code: joinCode }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new ApiError(
      errData.detail || `Failed to submit join request (${res.status})`,
      res.status,
    );
  }

  const body: { data: JoinRequestApiResponse } = await res.json();
  const request = body.data;

  // Fetch user details and enrich the response
  const user = await fetchUser(request.user_id);

  return {
    ...request,
    user_name: getDisplayName(user),
  };
}

export async function fetchJoinRequests(
  signal?: AbortSignal,
): Promise<JoinRequest[]> {
  const res = await fetch(`${API_BASE}/neighbourhood/join-requests`, {
    headers: getAuthHeaders(),
    signal,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new ApiError(
      errData.detail || `Failed to fetch join requests (${res.status})`,
      res.status,
    );
  }

  const requests: JoinRequestApiResponse[] = await res.json();

  // Fetch user details for all requests in parallel
  const enrichedRequests = await Promise.all(
    requests.map(
      async (request: JoinRequestApiResponse): Promise<JoinRequest> => {
        const user = await fetchUser(request.user_id);
        return {
          ...request,
          user_name: getDisplayName(user),
        };
      },
    ),
  );

  return enrichedRequests;
}

export async function resolveJoinRequest(
  requestId: string,
  action: "APPROVE" | "DENY",
): Promise<JoinRequest> {
  let res: Response;

  try {
    res = await fetch(`${API_BASE}/neighbourhood/join-requests/${requestId}`, {
      method: "PATCH",
      headers: getAuthHeaders(),
      body: JSON.stringify({ action }),
    });
  } catch (error) {
    console.error("Join request resolution network error", {
      requestId,
      action,
      error,
      apiBase: API_BASE,
    });
    throw new ApiError(
      "Unable to reach the server while updating the join request. Please try again.",
    );
  }

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    console.error("Join request resolution failed", {
      requestId,
      action,
      status: res.status,
      error: errData,
    });
    throw new ApiError(
      errData.detail || `Failed to resolve join request (${res.status})`,
      res.status,
    );
  }

  const body: { data: JoinRequestApiResponse } = await res.json();
  const request = body.data;

  // Fetch user details and enrich the response
  const user = await fetchUser(request.user_id);

  return {
    ...request,
    user_name: getDisplayName(user),
  };
}
