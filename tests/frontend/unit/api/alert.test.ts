import {
  acknowledgeAlert,
  apiFetch,
  broadcastAlert,
  fetchAlertFrequencyData,
  fetchAlertPropertyDistance,
  fetchAlertPropertyRoute,
  fetchAlerts,
  fetchCriticalAlertMap,
  fetchCurrentUser,
  fetchIncidents,
  fetchPropertyAlerts,
  fetchSituationalBrief,
  fetchTrackingTimeline,
  fetchUnlocatedCriticalAlerts,
  normaliseAlert,
} from "@/lib/api/alert";
import { apiCall } from "@/lib/api/client";

jest.mock("@/lib/api/client", () => ({
  apiCall: jest.fn(),
}));

jest.mock("@/lib/api/auth", () => ({
  getApiBaseUrl: jest.fn(() => "http://localhost:8000"),
  getAuthHeaders: jest.fn((headers) => ({
    "Content-Type": "application/json",
    Authorization: "Bearer test-token",
    ...headers,
  })),
  getAuthToken: jest.fn(() => "test-token"),
}));

const mockedFetch = fetch as jest.MockedFunction<typeof fetch>;
const mockedApiCall = jest.mocked(apiCall);
const consoleError = jest
  .spyOn(console, "error")
  .mockImplementation(() => undefined);

const UUID = "00000000-0000-0000-0000-000000000001";
const ISO_DATE = "2026-09-30T10:00:00Z";

function response(
  body: unknown,
  status = 200,
  contentType = "application/json",
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Bad Request",
    headers: new Headers({ "content-type": contentType }),
    json: jest.fn().mockResolvedValue(body),
    text: jest.fn().mockResolvedValue(
      typeof body === "string" ? body : JSON.stringify(body),
    ),
  } as unknown as Response;
}

const rawAlert = {
  id: UUID,
  camera_id: UUID,
  status: "OPEN",
  detection_type: "WEAPON_DETECTED",
  created_at: ISO_DATE,
};

const criticalMapResponse = {
  status: 200,
  message: null,
  data: {
    alerts: [
      {
        id: UUID,
        camera_id: UUID,
        camera_name: "Front camera",
        neighbourhood_id: UUID,
        detection_type: "WEAPON_DETECTED",
        status: "OPEN",
        created_at: ISO_DATE,
        property_id: UUID,
        property_address: "1 Main Street",
        latitude: -25.7479,
        longitude: 28.2293,
      },
    ],
    last_updated: ISO_DATE,
  },
};

const distanceData = {
  property_id: UUID,
  property_address: "1 Main Street",
  property_latitude: -25.7479,
  property_longitude: 28.2293,
  officer_latitude: -25.75,
  officer_longitude: 28.23,
  distance_metres: 250,
  officer_location_updated_at: ISO_DATE,
};

const routeData = {
  ...distanceData,
  route_distance_metres: 300,
  eta_seconds: 120,
  route_geometry: {
    type: "LineString",
    coordinates: [[28.2293, -25.7479]],
  },
  routing_error: null,
};

describe("alert API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    consoleError.mockClear();
  });

  it("returns JSON from a successful API response", async () => {
    mockedFetch.mockResolvedValueOnce(response({ ok: true }));

    await expect(apiFetch("/health")).resolves.toEqual({ ok: true });
    expect(mockedFetch).toHaveBeenCalledWith(
      "http://localhost:8000/health",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-token",
        }),
      }),
    );
  });

  it("returns undefined for a successful non-JSON response", async () => {
    mockedFetch.mockResolvedValueOnce(response("", 204, "text/plain"));

    await expect(apiFetch("/empty")).resolves.toBeUndefined();
  });

  it("converts network failures into a useful error", async () => {
    mockedFetch.mockRejectedValueOnce(new Error("network down"));

    await expect(apiFetch("/offline")).rejects.toThrow(
      "Unable to reach the server for /offline",
    );
    expect(consoleError).toHaveBeenCalled();
  });

  it("rethrows abort errors unchanged", async () => {
    const abortError = new DOMException("Aborted", "AbortError");
    mockedFetch.mockRejectedValueOnce(abortError);

    await expect(apiFetch("/cancelled")).rejects.toBe(abortError);
  });

  it("throws ApiError for an unsuccessful response", async () => {
    mockedFetch.mockResolvedValueOnce(
      response("Backend failed", 500, "text/plain"),
    );

    await expect(apiFetch("/failure")).rejects.toMatchObject({
      name: "ApiError",
      message: "API 500: Backend failed",
      statusCode: 500,
    });
    expect(consoleError).toHaveBeenCalled();
  });

  it("normalises OPEN alerts to the frontend NEW status", () => {
    expect(normaliseAlert(rawAlert).status).toBe("NEW");
    expect(normaliseAlert({ ...rawAlert, status: "RESOLVED" }).status).toBe(
      "RESOLVED",
    );
  });

  it("fetches the current user", async () => {
    mockedFetch.mockResolvedValueOnce(
      response({ neighbourhood_id: UUID }),
    );

    await expect(fetchCurrentUser()).resolves.toEqual({
      neighbourhood_id: UUID,
    });
  });

  it("fetches alerts with all filters and pagination defaults", async () => {
    mockedFetch.mockResolvedValueOnce(
      response({
        status: 200,
        message: null,
        data: [rawAlert],
        pagination: null,
      }),
    );

    const startDate = new Date("2026-09-01T00:00:00Z");
    const endDate = new Date("2026-09-30T00:00:00Z");
    const result = await fetchAlerts(
      "neighbourhood/one",
      {
        status: "NEW",
        cameraId: "camera-1",
        detectionType: "WEAPON_DETECTED",
        startDate,
        endDate,
        limit: 10,
        offset: 20,
      },
    );

    expect(result).toEqual({
      alerts: [{ ...rawAlert, status: "NEW" }],
      pagination: { total: 0, limit: 25, offset: 0, has_more: false },
    });
    expect(mockedFetch.mock.calls[0][0]).toEqual(
      expect.stringContaining(
        "/alerts/neighbourhood/one?status=OPEN&camera_id=camera-1",
      ),
    );
  });

  it("uses alert and pagination data returned by the backend", async () => {
    mockedFetch.mockResolvedValueOnce(
      response({
        status: 200,
        message: null,
        data: [rawAlert],
        pagination: { total: 1, limit: 1, offset: 0, has_more: false },
      }),
    );

    await expect(fetchPropertyAlerts("property-1")).resolves.toEqual({
      alerts: [{ ...rawAlert, status: "NEW" }],
      pagination: { total: 1, limit: 1, offset: 0, has_more: false },
    });
  });

  it("fetches incidents and normalises each representative alert", async () => {
    mockedFetch.mockResolvedValueOnce(
      response({
        status: 200,
        message: null,
        data: [
          {
            id: "incident-1",
            detection_type: "WEAPON_DETECTED",
            started_at: ISO_DATE,
            last_seen_at: ISO_DATE,
            alert_count: 1,
            representative_alert_id: UUID,
            representative_alert: rawAlert,
          },
        ],
        pagination: { total: 1, limit: 25, offset: 0, has_more: false },
      }),
    );

    const result = await fetchIncidents("neighbourhood-1");
    expect(result.incidents[0].representative_alert.status).toBe("NEW");
    expect(result.pagination.total).toBe(1);
  });

  it("sends acknowledge and broadcast requests", async () => {
    mockedFetch
      .mockResolvedValueOnce(response(undefined, 204, "text/plain"))
      .mockResolvedValueOnce(response(undefined, 204, "text/plain"));

    await expect(acknowledgeAlert(UUID)).resolves.toBeUndefined();
    await expect(broadcastAlert(UUID)).resolves.toBeUndefined();

    expect(mockedFetch).toHaveBeenNthCalledWith(
      1,
      `http://localhost:8000/alerts/${UUID}/acknowledge`,
      expect.objectContaining({ method: "PATCH" }),
    );
    expect(mockedFetch).toHaveBeenNthCalledWith(
      2,
      "http://localhost:8000/alerts/broadcast",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ alert_id: UUID }),
      }),
    );
  });

  it("fetches frequency metrics with and without optional filters", async () => {
    mockedApiCall
      .mockResolvedValueOnce({ status: 200, data: null })
      .mockResolvedValueOnce({ status: 200, data: [] });

    await expect(fetchAlertFrequencyData("neighbourhood-1")).resolves.toEqual({
      status: 200,
      data: null,
    });
    await expect(
      fetchAlertFrequencyData("neighbourhood-1", "DAILY", "MONTH"),
    ).resolves.toEqual({ status: 200, data: [] });

    expect(mockedApiCall).toHaveBeenNthCalledWith(
      2,
      "/alerts/frequency-metrics?neighbourhood_id=neighbourhood-1&time_interval=DAILY&time_period=MONTH",
      { method: "GET" },
    );
  });

  it("returns tracking data and rejects missing tracking data", async () => {
    mockedFetch
      .mockResolvedValueOnce(
        response({ status: 200, data: { alert_id: UUID, sightings: [] } }),
      )
      .mockResolvedValueOnce(
        response({ status: 404, message: "No tracking" }),
      );

    await expect(fetchTrackingTimeline(UUID)).resolves.toEqual({
      alert_id: UUID,
      sightings: [],
    });
    await expect(fetchTrackingTimeline(UUID)).rejects.toThrow("No tracking");
  });

  it("parses critical map, unlocated alerts, distance, and route responses", async () => {
    const unlocated = {
      ...criticalMapResponse,
      data: {
        ...criticalMapResponse.data,
        alerts: [
          {
            ...criticalMapResponse.data.alerts[0],
            latitude: null,
            longitude: null,
          },
        ],
      },
    };

    mockedApiCall
      .mockResolvedValueOnce(criticalMapResponse)
      .mockResolvedValueOnce(unlocated)
      .mockResolvedValueOnce({ status: 200, data: distanceData })
      .mockResolvedValueOnce({ status: 200, data: routeData });

    await expect(fetchCriticalAlertMap("neighbourhood/one")).resolves.toEqual(
      criticalMapResponse,
    );
    await expect(
      fetchUnlocatedCriticalAlerts("neighbourhood/one"),
    ).resolves.toEqual(unlocated);
    await expect(fetchAlertPropertyDistance(UUID)).resolves.toEqual({
      status: 200,
      data: distanceData,
    });
    await expect(fetchAlertPropertyRoute(UUID)).resolves.toEqual({
      status: 200,
      data: routeData,
    });
  });

  it("returns situational briefs and rejects an unavailable brief", async () => {
    const brief = {
      tracking_subject_id: UUID,
      generated_at: ISO_DATE,
      trigger: "WEAPON_DETECTED",
      summary: "Summary",
      cameras: [],
      alerts: [],
      sightings: [],
      last_known_location: {
        camera_id: UUID,
        camera_name: "Front camera",
        camera_location: "Gate",
        property_id: UUID,
        observed_at: ISO_DATE,
      },
    };

    mockedFetch
      .mockResolvedValueOnce(response({ status: 200, data: brief }))
      .mockResolvedValueOnce(
        response({ status: 404, message: "Brief unavailable" }),
      );

    await expect(fetchSituationalBrief(UUID)).resolves.toEqual(brief);
    await expect(fetchSituationalBrief(UUID)).rejects.toThrow(
      "Brief unavailable",
    );
  });
});