import {
  act,
  cleanup,
  renderHook,
  waitFor,
} from "@testing-library/react";

import type { Location } from "@capgo/background-geolocation";

import {
  updateSecurityLocation,
} from "@/lib/api/neighbourhood";
import {
  useOfficerLocationTracking,
} from "@/hooks/use-officer-location-tracking";
import {
  useLocationPermission,
} from "@/hooks/use-location-permission";

type StartCallback = (
  position?: Location,
  error?: { message: string; code?: string },
) => void;

jest.mock("@capgo/background-geolocation", () => ({
  BackgroundGeolocation: {
    start: jest.fn(),
    stop: jest.fn(),
  },
}));

jest.mock("@/lib/api/neighbourhood", () => ({
  updateSecurityLocation: jest.fn(),
}));

jest.mock("@/hooks/use-location-permission", () => ({
  useLocationPermission: jest.fn(),
}));

const { BackgroundGeolocation } = jest.requireMock(
  "@capgo/background-geolocation",
) as {
  BackgroundGeolocation: {
    start: jest.Mock;
    stop: jest.Mock;
  };
};

const mockStart = BackgroundGeolocation.start;
const mockStop = BackgroundGeolocation.stop;

const mockUpdateLocation =
  updateSecurityLocation as jest.MockedFunction<
    typeof updateSecurityLocation
  >;

const mockUseLocationPermission =
  useLocationPermission as jest.MockedFunction<
    typeof useLocationPermission
  >;

const NEIGHBOURHOOD_ID =
  "40a3036a-99ed-455f-891b-166826ff0886";

describe("useOfficerLocationTracking", () => {
  let startCallback: StartCallback | null;
  let mockRequestBackground: jest.Mock;

  const setPermissionState = (
    backgroundStatus: "granted" | "denied" | "prompt",
  ) => {
    mockUseLocationPermission.mockReturnValue({
      status: "granted",
      backgroundStatus,
      loading: false,
      refresh: jest.fn(),
      request: jest.fn(),
      requestBackground: mockRequestBackground,
    });
  };

  beforeEach(() => {
    jest.resetAllMocks();
    startCallback = null;
    mockRequestBackground = jest.fn().mockResolvedValue("granted");

    mockStart.mockImplementation(
      async (_options: unknown, callback: StartCallback) => {
        startCallback = callback;
      },
    );

    mockStop.mockResolvedValue(undefined);

    mockUpdateLocation.mockResolvedValue({
      status: 200,
      message: "Location updated",
    });

    setPermissionState("granted");
  });

  afterEach(() => {
    cleanup();
  });

  test(
    "starts background tracking and sends officer location while on duty",
    async () => {
      renderHook(() =>
        useOfficerLocationTracking(
          NEIGHBOURHOOD_ID,
          true,
        ),
      );

      await waitFor(() => {
        expect(mockStart).toHaveBeenCalledTimes(1);
      });

      expect(mockStart).toHaveBeenCalledWith(
        expect.objectContaining({
          backgroundMessage: expect.any(String),
          requestPermissions: false,
        }),
        expect.any(Function),
      );

      const location = {
          latitude: -25.7479,
          longitude: 28.2293,
      } as Location;

      act(() => {
        startCallback?.(location);
      });

      await waitFor(() => {
        expect(mockUpdateLocation).toHaveBeenCalledWith({
          neighbourhood_id: NEIGHBOURHOOD_ID,
          latitude: -25.7479,
          longitude: 28.2293,
        });
      });
    },
  );

  test(
    "requests background permission when not already granted",
    async () => {
      setPermissionState("denied");

      renderHook(() =>
        useOfficerLocationTracking(
          NEIGHBOURHOOD_ID,
          true,
        ),
      );

      await waitFor(() => {
        expect(mockRequestBackground).toHaveBeenCalledTimes(1);
      });

      await waitFor(() => {
        expect(mockStart).toHaveBeenCalledTimes(1);
      });
    },
  );

  test(
    "stops tracking when unmounted",
    async () => {
      const { unmount } = renderHook(() =>
        useOfficerLocationTracking(
          NEIGHBOURHOOD_ID,
          true,
        ),
      );

      await waitFor(() => {
        expect(mockStart).toHaveBeenCalledTimes(1);
      });

      unmount();

      await waitFor(() => {
        expect(mockStop).toHaveBeenCalledTimes(1);
      });
    },
  );

  test(
    "does not start tracking while off duty",
    () => {
      renderHook(() =>
        useOfficerLocationTracking(
          NEIGHBOURHOOD_ID,
          false,
        ),
      );

      expect(mockStart).not.toHaveBeenCalled();
      expect(mockUpdateLocation).not.toHaveBeenCalled();
    },
  );
});
