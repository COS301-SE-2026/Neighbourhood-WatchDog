import {
  fetchDangerZones,
} from "@/lib/api/danger-zone";

import {
  apiCall,
} from "@/lib/api/client";

jest.mock("@/lib/api/client", () => ({
  apiCall: jest.fn(),
}));

const mockedApiCall = jest.mocked(apiCall);

const NEIGHBOURHOOD_ID =
  "00000000-0000-4000-8000-000000000001";

const RESPONSE = {
  status: 200,
  message: "Danger zones retrieved successfully",
  data: {
    neighbourhood_id: NEIGHBOURHOOD_ID,
    window_start: "2026-08-27",
    window_end: "2026-09-25",
    calculated_at:
      "2026-09-25T14:00:00Z",
    cell_size_metres: 100,
    min_score: 0.15,
    max_score: 0.9,
    cells: [
      {
        cell_id: "3142700:-2963800",
        grid_x: 3142700,
        grid_y: -2963800,
        latitude: -25.75,
        longitude: 28.23,
        south: -25.7504,
        west: 28.2295,
        north: -25.7496,
        east: 28.2305,
        incident_count: 10,
        incident_score: 1,
        coverage_ratio: 0.1,
        coverage_sparsity: 0.9,
        danger_score: 0.9,
      },
    ],
  },
};

describe("danger-zone API client", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("requests danger zones for the viewport", async () => {
    mockedApiCall.mockResolvedValueOnce(
      RESPONSE,
    );

    const result = await fetchDangerZones(
      NEIGHBOURHOOD_ID,
      {
        west: 28.20,
        south: -25.80,
        east: 28.30,
        north: -25.70,
      },
    );

    expect(result).toEqual(RESPONSE.data);

    expect(mockedApiCall).toHaveBeenCalledWith(
      expect.stringContaining(
        `/alerts/neighbourhoods/${NEIGHBOURHOOD_ID}` +
          "/danger-zones?",
      ),
    );

    const requestUrl =
      mockedApiCall.mock.calls[0][0] as string;

    expect(requestUrl).toContain(
      "west=28.2",
    );
    expect(requestUrl).toContain(
      "south=-25.8",
    );
    expect(requestUrl).toContain(
      "east=28.3",
    );
    expect(requestUrl).toContain(
      "north=-25.7",
    );
  });

  test("rejects an invalid danger-score response", async () => {
    mockedApiCall.mockResolvedValueOnce({
      ...RESPONSE,
      data: {
        ...RESPONSE.data,
        cells: [
          {
            ...RESPONSE.data.cells[0],
            danger_score: 2.5,
          },
        ],
      },
    });

    await expect(
      fetchDangerZones(
        NEIGHBOURHOOD_ID,
        {
          west: 28.20,
          south: -25.80,
          east: 28.30,
          north: -25.70,
        },
      ),
    ).rejects.toThrow();
  });

  test("rejects an invalid viewport response shape", async () => {
    mockedApiCall.mockResolvedValueOnce({
      status: 200,
      message: null,
      data: {
        ...RESPONSE.data,
        cells: "not-an-array",
      },
    });

    await expect(
      fetchDangerZones(
        NEIGHBOURHOOD_ID,
        {
          west: 28.20,
          south: -25.80,
          east: 28.30,
          north: -25.70,
        },
      ),
    ).rejects.toThrow();
  });
});