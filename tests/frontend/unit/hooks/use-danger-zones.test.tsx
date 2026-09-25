import {
  act,
  renderHook,
  waitFor,
} from "@testing-library/react";

import {
  fetchDangerZones,
} from "@/lib/api/danger-zone";

import {
  useDangerZones,
} from "@/hooks/use-danger-zones";

import type {
  DangerZoneData,
} from "@/lib/validators/danger-zone";

jest.mock("@/lib/api/danger-zone", () => ({
  fetchDangerZones: jest.fn(),
}));

const mockedFetchDangerZones =
  jest.mocked(fetchDangerZones);

const viewport = {
  west: 28.20,
  south: -25.80,
  east: 28.30,
  north: -25.70,
};

const data: DangerZoneData = {
  neighbourhood_id:
    "00000000-0000-0000-0000-000000000001",
  window_start: "2026-08-27",
  window_end: "2026-09-25",
  calculated_at:
    "2026-09-25T14:00:00Z",
  cell_size_metres: 100,
  min_score: 0.15,
  max_score: 0.90,
  cells: [],
};

describe("useDangerZones", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("does not request while disabled", () => {
    const { result } = renderHook(() =>
      useDangerZones({
        neighbourhoodId: "neighbourhood-1",
        viewport,
        enabled: false,
      }),
    );

    expect(
      mockedFetchDangerZones,
    ).not.toHaveBeenCalled();

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test("does not request without a viewport", () => {
    renderHook(() =>
      useDangerZones({
        neighbourhoodId: "neighbourhood-1",
        viewport: null,
        enabled: true,
      }),
    );

    expect(
      mockedFetchDangerZones,
    ).not.toHaveBeenCalled();
  });

  test("loads danger data after the debounce", async () => {
    mockedFetchDangerZones.mockResolvedValueOnce(
      data,
    );

    const { result } = renderHook(() =>
      useDangerZones({
        neighbourhoodId: "neighbourhood-1",
        viewport,
        enabled: true,
      }),
    );

    await act(async () => {
      jest.advanceTimersByTime(350);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(result.current.data).toEqual(data);
    });

    expect(
      mockedFetchDangerZones,
    ).toHaveBeenCalledWith(
      "neighbourhood-1",
      viewport,
    );

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test("exposes request errors", async () => {
    mockedFetchDangerZones.mockRejectedValueOnce(
      new Error("Network unavailable"),
    );

    const { result } = renderHook(() =>
      useDangerZones({
        neighbourhoodId: "neighbourhood-1",
        viewport,
        enabled: true,
      }),
    );

    await act(async () => {
      jest.advanceTimersByTime(350);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(result.current.error).toBe(
        "Network unavailable",
      );
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});