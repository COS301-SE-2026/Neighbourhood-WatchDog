import { getPairingToken } from "@/lib/api/pairAgent";
import {
  fetchNeighbourhoodRiskScore,
  fetchNeighbourhoodRiskScoreHistory,
} from "@/lib/api/riskScore";
import {
  fetchNeighbourhoodRiskThreshold,
  updateNeighbourhoodRiskThreshold,
} from "@/lib/api/riskThreshold";
import { fetchMyContext } from "@/lib/api/user-context";
import { registerPushDevice } from "@/lib/api/user";
import {
  fetchUserSettings,
  updateUserSettings,
} from "@/lib/api/userSettings";
import { apiCall } from "@/lib/api/client";

jest.mock("@/lib/api/client", () => ({
  apiCall: jest.fn(),
}));

const mockedApiCall = jest.mocked(apiCall);
const ID = "10000000-0000-4000-8000-000000000001";
const context = {
  user: {
    id: ID,
    name: "Test User",
    system_role: "RESIDENT",
  },
  properties: [],
};
const settings = {
  first_name: "Test",
  last_name: "User",
  email: "test@example.com",
  phone_number: null,
  system_role: "RESIDENT",
};

describe("simple API wrappers", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("gets a property pairing token", async () => {
    const response = {
      status: 200,
      message: null,
      data: { token: "ABC123", expires_at: "2026-10-01T10:00:00Z" },
    };
    mockedApiCall.mockResolvedValueOnce(response);

    await expect(getPairingToken(ID)).resolves.toEqual(response);
    expect(mockedApiCall).toHaveBeenCalledWith(`/pairing-token/${ID}`, {
      method: "GET",
    });
  });

  it("gets a neighbourhood risk score", async () => {
    const response = {
      status: 200,
      message: "OK",
      data: null,
    };
    mockedApiCall.mockResolvedValueOnce(response);

    await expect(fetchNeighbourhoodRiskScore(ID)).resolves.toEqual(response);
    expect(mockedApiCall).toHaveBeenCalledWith(
      `/risk-score/neighbourhood/${ID}`,
      { method: "GET" },
    );
  });

  it("gets risk-score history with and without date filters", async () => {
    mockedApiCall
      .mockResolvedValueOnce({ status: 200, message: "OK", data: [] })
      .mockResolvedValueOnce({ status: 200, message: "OK", data: [] });

    await expect(
      fetchNeighbourhoodRiskScoreHistory(ID, "day"),
    ).resolves.toEqual({ status: 200, message: "OK", data: [] });
    await expect(
      fetchNeighbourhoodRiskScoreHistory(ID, "week", "2026-09-01", "2026-09-30"),
    ).resolves.toEqual({ status: 200, message: "OK", data: [] });

    expect(mockedApiCall).toHaveBeenNthCalledWith(
      2,
      `/risk-score/neighbourhood/${ID}/history?granularity=week&start=2026-09-01&end=2026-09-30`,
      { method: "GET" },
    );
  });

  it("gets and updates risk thresholds", async () => {
    const response = {
      status: 200,
      message: "OK",
      data: {
        id: ID,
        neighbourhood_id: ID,
        low_max: 0.3,
        medium_max: 0.7,
        updated_at: "2026-09-30T10:00:00Z",
      },
    };
    const input = { low_max: 0.3, medium_max: 0.7 };
    mockedApiCall
      .mockResolvedValueOnce(response)
      .mockResolvedValueOnce(response);

    await expect(fetchNeighbourhoodRiskThreshold(ID)).resolves.toEqual(
      response,
    );
    await expect(
      updateNeighbourhoodRiskThreshold(ID, input),
    ).resolves.toEqual(response);
  });

  it("parses the current user context", async () => {
    mockedApiCall.mockResolvedValueOnce(context);

    await expect(fetchMyContext()).resolves.toEqual(context);
  });

  it("rejects an invalid current user context", async () => {
    mockedApiCall.mockResolvedValueOnce({ user: {}, properties: [] });

    await expect(fetchMyContext()).rejects.toThrow();
  });

  it("registers a push device", async () => {
    const response = { status: 200, message: "Registered" };
    mockedApiCall.mockResolvedValueOnce(response);

    await expect(registerPushDevice("device-token")).resolves.toEqual(
      response,
    );
    expect(mockedApiCall).toHaveBeenCalledWith("/users/me/push-device", {
      method: "POST",
      body: { device_token: "device-token" },
    });
  });

  it("gets and updates user settings", async () => {
    const input = {
      first_name: "Updated",
      last_name: "User",
      phone_number: "+27123456789",
    };
    mockedApiCall
      .mockResolvedValueOnce(settings)
      .mockResolvedValueOnce(settings);

    await expect(fetchUserSettings()).resolves.toEqual(settings);
    await expect(updateUserSettings(input)).resolves.toEqual(settings);

    expect(mockedApiCall).toHaveBeenNthCalledWith(
      2,
      "/users/me/settings",
      { method: "PATCH", body: input },
    );
  });
});