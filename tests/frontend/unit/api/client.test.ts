import { apiCall } from "@/lib/api/client";
import {
  clearSession,
  getAccessToken,
  refreshSession,
} from "@/lib/auth/cognito";

jest.mock("@/lib/auth/cognito", () => ({
  clearSession: jest.fn(),
  getAccessToken: jest.fn(),
  refreshSession: jest.fn(),
}));

const mockedFetch = fetch as jest.MockedFunction<typeof fetch>;
const mockedGetAccessToken = jest.mocked(getAccessToken);
const mockedRefreshSession = jest.mocked(refreshSession);
const mockedClearSession = jest.mocked(clearSession);

function response(
  body: unknown,
  status = 200,
  statusText = "OK",
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json: jest.fn().mockResolvedValue(body),
  } as unknown as Response;
}

describe("apiCall", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGetAccessToken.mockReturnValue("access-token");
  });

  it("sends an authenticated JSON request and returns JSON", async () => {
    mockedFetch.mockResolvedValueOnce(response({ ok: true }));

    await expect(
      apiCall<{ ok: boolean }>("/test", {
        method: "POST",
        body: { value: 1 },
      }),
    ).resolves.toEqual({ ok: true });

    expect(mockedFetch).toHaveBeenCalledWith(
      expect.stringContaining("/test"),
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ value: 1 }),
        headers: expect.objectContaining({
          Authorization: "Bearer access-token",
        }),
      }),
    );
  });

  it("refreshes when no access token is available", async () => {
    mockedGetAccessToken.mockReturnValue(null);
    mockedRefreshSession.mockResolvedValueOnce("refreshed-token");
    mockedFetch.mockResolvedValueOnce(response({ refreshed: true }));

    await expect(apiCall("/refresh-needed")).resolves.toEqual({
      refreshed: true,
    });

    expect(mockedRefreshSession).toHaveBeenCalledTimes(1);
    expect(mockedFetch).toHaveBeenCalledWith(
      expect.stringContaining("/refresh-needed"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer refreshed-token",
        }),
      }),
    );
  });

  it("clears the session when the initial refresh fails", async () => {
    mockedGetAccessToken.mockReturnValue(null);
    mockedRefreshSession.mockRejectedValueOnce(new Error("expired"));

    await expect(apiCall("/protected")).rejects.toThrow(
      "Your session has expired. Please log in again.",
    );

    expect(mockedClearSession).toHaveBeenCalledTimes(1);
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  it("refreshes and retries after a 401 response", async () => {
    mockedRefreshSession.mockResolvedValueOnce("new-token");
    mockedFetch
      .mockResolvedValueOnce(response({}, 401, "Unauthorized"))
      .mockResolvedValueOnce(response({ retried: true }));

    await expect(apiCall("/retry")).resolves.toEqual({ retried: true });
    expect(mockedRefreshSession).toHaveBeenCalledTimes(1);
    expect(mockedFetch).toHaveBeenCalledTimes(2);
  });

  it("clears the session when a 401 refresh fails", async () => {
    mockedRefreshSession.mockRejectedValueOnce(new Error("expired"));
    mockedFetch.mockResolvedValueOnce(response({}, 401, "Unauthorized"));

    await expect(apiCall("/retry-fails")).rejects.toThrow(
      "Your session has expired. Please log in again.",
    );

    expect(mockedClearSession).toHaveBeenCalledTimes(1);
    expect(mockedFetch).toHaveBeenCalledTimes(1);
  });

  it.each([
    [{ detail: { message: "nested detail" } }, "nested detail"],
    [{ detail: "plain detail" }, "plain detail"],
    [{ message: "message field" }, "message field"],
    [{}, "Bad Request"],
  ])("uses a useful error message for an unsuccessful response", async (body, message) => {
    mockedFetch.mockResolvedValueOnce(response(body, 400, "Bad Request"));

    await expect(apiCall("/bad-request")).rejects.toThrow(message);
  });

  it("falls back to the status text when an error body is invalid", async () => {
    mockedFetch.mockResolvedValueOnce({
      ok: false,
      status: 502,
      statusText: "Bad Gateway",
      json: jest.fn().mockRejectedValue(new Error("invalid JSON")),
    } as unknown as Response);

    await expect(apiCall("/invalid-error-body")).rejects.toThrow(
      "Bad Gateway",
    );
  });

  it("returns undefined for a 204 response", async () => {
    const emptyResponse = response(undefined, 204, "No Content");
    mockedFetch.mockResolvedValueOnce(emptyResponse);

    await expect(apiCall("/delete")).resolves.toBeUndefined();
    expect(emptyResponse.json).not.toHaveBeenCalled();
  });
});