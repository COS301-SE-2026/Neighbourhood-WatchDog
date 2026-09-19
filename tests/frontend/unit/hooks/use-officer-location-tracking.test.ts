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


});
