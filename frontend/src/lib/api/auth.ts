const FALLBACK_AUTH_TOKEN = "mocktoke";

export function getAuthToken(): string {
  if (typeof window === "undefined") return FALLBACK_AUTH_TOKEN;

  return (
    localStorage.getItem("accessToken") ||
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
  const url = process.env.NEXT_PUBLIC_API_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
  return url || "https://api-staging.neighbourhoodwatchdog.co.za"
}
