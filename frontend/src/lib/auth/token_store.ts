let accessToken: string | null = null;
let expiresAt = 0;

export function storeAccessToken(
  token: string,
  expiresInSeconds = 3600,
): void {
  accessToken = token;
  expiresAt = Date.now() + expiresInSeconds * 1000;
}

export function readAccessToken(): string | null {
  if (!accessToken) {
    return null;
  }

  // Give requests 30 seconds of safety before expiration.
  if (Date.now() >= expiresAt - 30_000) {
    clearAccessToken();
    return null;
  }

  return accessToken;
}

export function clearAccessToken(): void {
  accessToken = null;
  expiresAt = 0;
}
