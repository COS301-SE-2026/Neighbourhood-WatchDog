import {
  act,
  cleanup,
  renderHook,
  waitFor,
} from "@testing-library/react";

import {
  Geolocation,
  type Position,
  type WatchPositionCallback,
} from "@capacitor/geolocation";

import {
  updateSecurityLocation,
} from "@/lib/api/neighbourhood";
import {
  useOfficerLocationTracking,
} from "@/hooks/use-officer-location-tracking";

jest.mock("@capacitor/geolocation", () => ({
  Geolocation: {
    watchPosition: jest.fn(),
    clearWatch: jest.fn(),
  },
}));

jest.mock("@/lib/api/neighbourhood", () => ({
  updateSecurityLocation: jest.fn(),
}));

const NEIGHBOURHOOD_ID =
  "40a3036a-99ed-455f-891b-166826ff0886";

const mockWatchPosition =
  Geolocation.watchPosition as jest.MockedFunction<
    typeof Geolocation.watchPosition
  >;

const mockClearWatch =
  Geolocation.clearWatch as jest.MockedFunction<
    typeof Geolocation.clearWatch
  >;

const mockUpdateLocation =
  updateSecurityLocation as jest.MockedFunction<
    typeof updateSecurityLocation
  >;

describe("useOfficerLocationTracking", () => {
  let watchCallback:
    | WatchPositionCallback
    | null;

  beforeEach(() => {
    jest.resetAllMocks();
    watchCallback = null;

    mockWatchPosition.mockImplementation(
      async (_options, callback) => {
        watchCallback = callback;
        return "officer-watch";
      },
    );

    mockClearWatch.mockResolvedValue();

    mockUpdateLocation.mockResolvedValue({
      status: 200,
      message: "Location updated",
    });
  });

  afterEach(() => {
    cleanup();
  });

  test(
    "watches and sends officer location while on duty",
    async () => {
      renderHook(() =>
        useOfficerLocationTracking(
          NEIGHBOURHOOD_ID,
          true,
        ),
      );

      await waitFor(() => {
        expect(
          mockWatchPosition,
        ).toHaveBeenCalledTimes(1);
      });

      expect(
        mockWatchPosition,
      ).toHaveBeenCalledWith(
        expect.objectContaining({
          enableHighAccuracy: true,
          minimumUpdateInterval: 10_000,
          interval: 10_000,
        }),
        expect.any(Function),
      );

      const position = {
        coords: {
          latitude: -25.7479,
          longitude: 28.2293,
        },
      } as Position;

      act(() => {
        watchCallback?.(
          position,
        );
      });

      await waitFor(() => {
        expect(
          mockUpdateLocation,
        ).toHaveBeenCalledWith({
          neighbourhood_id:
            NEIGHBOURHOOD_ID,
          latitude: -25.7479,
          longitude: 28.2293,
        });
      });
    },
  );

  test(
    "clears the location watcher when unmounted",
    async () => {
      const { unmount } = renderHook(() =>
        useOfficerLocationTracking(
          NEIGHBOURHOOD_ID,
          true,
        ),
      );

      await waitFor(() => {
        expect(
          mockWatchPosition,
        ).toHaveBeenCalledTimes(1);
      });

      unmount();

      await waitFor(() => {
        expect(
          mockClearWatch,
        ).toHaveBeenCalledWith({
          id: "officer-watch",
        });
      });
    },
  );

  test(
    "does not watch location while off duty",
    () => {
      renderHook(() =>
        useOfficerLocationTracking(
          NEIGHBOURHOOD_ID,
          false,
        ),
      );

      expect(
        mockWatchPosition,
      ).not.toHaveBeenCalled();

      expect(
        mockUpdateLocation,
      ).not.toHaveBeenCalled();
    },
  );
});
