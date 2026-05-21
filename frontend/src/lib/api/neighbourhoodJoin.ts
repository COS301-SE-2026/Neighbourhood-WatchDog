import type { JoinRequest } from "@/components/shared/RequestCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    const message: string =
      typeof body?.detail === "string"
        ? body.detail
        : typeof body?.message === "string"
          ? body.message
          : `Request failed (${res.status})`;
    return new ApiError(res.status, message);
  } catch {
    return new ApiError(res.status, `Request failed (${res.status})`);
  }
}

export async function submitJoinRequest(
  joinCode: string,
): Promise<JoinRequest> {
  const res = await fetch(`${API_BASE}/neighbourhood/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ join_code: joinCode }),
  });

  if (!res.ok) throw await parseError(res);

  const body = await res.json();
  return body.data as JoinRequest;
}
