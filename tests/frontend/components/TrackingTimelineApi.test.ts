import {
  ApiError,
  fetchTrackingTimeline,
} from "../../../frontend/src/lib/api/alert";

const responseFor = (body: unknown, status = 200): Response =>
  ({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 404 ? "Not Found" : "OK",
    headers: {
      get: () => "application/json",
    },
    json: jest.fn().mockResolvedValue(body),
    text: jest.fn().mockResolvedValue(JSON.stringify(body)),
  }) as unknown as Response;

describe("fetchTrackingTimeline", () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockReset();
  });

  test("returns timeline data from a successful response", async () => {
    const data = {
      alert_id: "alert-1",
      tracking_subject_id: "subject-1",
      alert_status: "OPEN",
      sightings: [],
    };
    (fetch as jest.Mock).mockResolvedValue(
      responseFor({ status: 200, message: "ok", data }),
    );

    await expect(fetchTrackingTimeline("alert-1")).resolves.toEqual(data);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/alerts/alert-1/tracking"),
      expect.objectContaining({ headers: expect.anything() }),
    );
  });

  test("converts a missing timeline into an ApiError", async () => {
    (fetch as jest.Mock).mockResolvedValue(
      responseFor(
        { status: 404, message: "No timeline", data: null },
        200,
      ),
    );

    await expect(fetchTrackingTimeline("alert-1")).rejects.toMatchObject({
      name: "ApiError",
      message: "No timeline",
      statusCode: 404,
    } satisfies Partial<ApiError>);
  });

  test("converts a failed HTTP response into an ApiError", async () => {
    (fetch as jest.Mock).mockResolvedValue(
      responseFor("forbidden", 403),
    );

    await expect(fetchTrackingTimeline("alert-1")).rejects.toBeInstanceOf(
      ApiError,
    );
  });
});
