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
    "X-Mock-Role": "NEIGHBOURHOOD_ADMIN",
    "X-Mock-Sub": "00000000-0000-0000-0000-000000000001",
    "X-Mock-Neighbourhood-Id": "10000000-0000-0000-0000-000000000001",
    ...extraHeaders,
  };
}

export function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "https://api-staging.neighbourhoodwatchdog.co.za"
  );
}
