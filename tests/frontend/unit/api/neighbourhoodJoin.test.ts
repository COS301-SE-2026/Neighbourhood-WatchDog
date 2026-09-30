import {
  fetchJoinCodeRequest,
  fetchJoinRequests,
  regenerateJoinCodeRequest,
  resolveJoinRequest,
  submitJoinRequest,
} from "@/lib/api/neighbourhoodJoin";
import { apiCall } from "@/lib/api/client";

jest.mock("@/lib/api/client", () => ({
  apiCall: jest.fn(),
}));

jest.mock("@/lib/api/auth", () => ({
  getApiBaseUrl: jest.fn(() => "http://localhost:8000"),
  getAuthHeaders: jest.fn(() => ({
    "Content-Type": "application/json",
    Authorization: "Bearer test-token",
  })),
}));

const mockedApiCall = jest.mocked(apiCall);
const mockedFetch = fetch as jest.MockedFunction<typeof fetch>;
const consoleWarn = jest
  .spyOn(console, "warn")
  .mockImplementation(() => undefined);
const consoleError = jest
  .spyOn(console, "error")
  .mockImplementation(() => undefined);
const PROPERTY_ID = "10000000-0000-4000-8000-000000000001";
const NEIGHBOURHOOD_ID = "10000000-0000-4000-8000-000000000002";
const USER_ID = "10000000-0000-4000-8000-000000000003";
const REQUEST_ID = "10000000-0000-4000-8000-000000000004";

function response(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Bad Request",
    json: jest.fn().mockResolvedValue(body),
    text: jest.fn().mockResolvedValue(
      typeof body === "string" ? body : JSON.stringify(body),
    ),
  } as unknown as Response;
}

const request = {
  id: REQUEST_ID,
  neighbourhood_id: NEIGHBOURHOOD_ID,
  user_id: USER_ID,
  status: "PENDING",
  created_at: "2026-09-30T10:00:00Z",
  resolved_at: null,
};

describe("neighbourhood join-request API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    consoleWarn.mockClear();
    consoleError.mockClear();
  });

  it("submits a join request and enriches it with the user's full name", async () => {
    mockedFetch
      .mockResolvedValueOnce(response({ data: request }))
      .mockResolvedValueOnce(
        response({
          first_name: "Test",
          last_name: "Resident",
          email: "resident@example.com",
        }),
      );

    await expect(
      submitJoinRequest(PROPERTY_ID, "JOIN123"),
    ).resolves.toEqual({ ...request, user_name: "Test Resident" });

    expect(mockedFetch).toHaveBeenNthCalledWith(
      1,
      `http://localhost:8000/neighbourhood/join/${PROPERTY_ID}`,
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ join_code: "JOIN123" }),
      }),
    );
  });

  it("uses Unknown User when the user lookup fails", async () => {
    mockedFetch
      .mockResolvedValueOnce(response({ data: request }))
      .mockResolvedValueOnce(response("Not found", 404));

    await expect(
      submitJoinRequest(PROPERTY_ID, "JOIN123"),
    ).resolves.toEqual({ ...request, user_name: "Unknown User" });
    expect(consoleWarn).toHaveBeenCalled();
  });

  it("uses an API error when submitting a join request fails", async () => {
    mockedFetch.mockResolvedValueOnce(
      response({ detail: "Join code is invalid" }, 400),
    );

    await expect(
      submitJoinRequest(PROPERTY_ID, "BAD"),
    ).rejects.toMatchObject({
      name: "ApiError",
      message: "Join code is invalid",
      statusCode: 400,
    });
  });

  it("fetches and enriches multiple join requests", async () => {
    const secondRequest = {
      ...request,
      id: "10000000-0000-4000-8000-000000000005",
      user_id: "10000000-0000-4000-8000-000000000006",
    };
    mockedFetch
      .mockResolvedValueOnce(response([request, secondRequest]))
      .mockResolvedValueOnce(
        response({
          first_name: "First",
          last_name: "Resident",
          email: "first@example.com",
        }),
      )
      .mockRejectedValueOnce(new Error("user lookup failed"));

    await expect(
      fetchJoinRequests(NEIGHBOURHOOD_ID),
    ).resolves.toEqual([
      { ...request, user_name: "First Resident" },
      { ...secondRequest, user_name: "Unknown User" },
    ]);
    expect(consoleWarn).toHaveBeenCalled();
  });

  it("reports errors while fetching join requests", async () => {
    mockedFetch.mockResolvedValueOnce(response({}, 500));

    await expect(fetchJoinRequests(NEIGHBOURHOOD_ID)).rejects.toMatchObject({
      name: "ApiError",
      statusCode: 500,
    });
  });

  it("resolves a join request", async () => {
    mockedFetch
      .mockResolvedValueOnce(response({ data: request }))
      .mockResolvedValueOnce(
        response({
          first_name: "Test",
          last_name: "Resident",
          email: "resident@example.com",
        }),
      );

    await expect(
      resolveJoinRequest(REQUEST_ID, "APPROVE"),
    ).resolves.toEqual({ ...request, user_name: "Test Resident" });
  });

  it("handles network and backend errors while resolving a request", async () => {
    mockedFetch.mockRejectedValueOnce(new Error("offline"));

    await expect(
      resolveJoinRequest(REQUEST_ID, "DENY"),
    ).rejects.toMatchObject({
      name: "ApiError",
      message:
        "Unable to reach the server while updating the join request. Please try again.",
    });

    mockedFetch.mockResolvedValueOnce(
      response({ detail: "Request already resolved" }, 409),
    );

    await expect(
      resolveJoinRequest(REQUEST_ID, "DENY"),
    ).rejects.toMatchObject({
      name: "ApiError",
      message: "Request already resolved",
      statusCode: 409,
    });
    expect(consoleError).toHaveBeenCalled();
  });

  it("gets and regenerates a neighbourhood join code", async () => {
    const result = { join_code: "JOIN123" };
    mockedApiCall
      .mockResolvedValueOnce(result)
      .mockResolvedValueOnce(result);

    await expect(fetchJoinCodeRequest(NEIGHBOURHOOD_ID)).resolves.toEqual(
      result,
    );
    await expect(
      regenerateJoinCodeRequest(NEIGHBOURHOOD_ID),
    ).resolves.toEqual(result);
  });
});