const FALLBACK_AUTH_TOKEN = "mocktoke";

export function getAuthToken(): string {
  if (typeof window === "undefined") return FALLBACK_AUTH_TOKEN;

  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("authToken") ||
    FALLBACK_AUTH_TOKEN
  );
}

export function getAuthHeaders(extraHeaders: HeadersInit = {}): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getAuthToken()}`,
    ...extraHeaders,
  };
}

export function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000"
  );
}
