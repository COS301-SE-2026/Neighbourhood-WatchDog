import { readAccessToken } from "../auth/token_store";

const FALLBACK_AUTH_TOKEN = "mocktoke";

export function getAuthToken(): string | null {
  return readAccessToken();
}

export function getAuthHeaders(extraHeaders: HeadersInit = {}): HeadersInit {

  const token = getAuthToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}`} : {}),
    ...extraHeaders
    
  };
}

export function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "https://api-staging.neighbourhoodwatchdog.co.za"
  );
}
