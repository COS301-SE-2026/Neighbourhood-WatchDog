import {
  act,
  cleanup,
  renderHook,
  waitFor,
} from "@testing-library/react";

import {
  fetchAlertPropertyDistance,
  fetchAlertPropertyRoute,
} from "@/lib/api/alert";
import { useAlertPropertyRoute } from "@/hooks/use-alert-property-route";

import type {
  AlertDistanceRes,
  AlertRouteRes,
} from "@/lib/validators/alert";

jest.mock("@/lib/api/alert", () => ({
  fetchAlertPropertyDistance: jest.fn(),
  fetchAlertPropertyRoute: jest.fn(),
}));

const PROPERTY_ID = "33333333-3333-4333-8333-333333333333";

const FIRST_UPDATE = "2026-09-19T10:00:00.000Z";

const SECOND_UPDATE = "2026-09-19T10:01:00.000Z";

function routeResponse(
  updatedAt: string,
  etaSeconds: number | null,
  routingError: string | null = null,
): AlertRouteRes {
  return {
    status: 200,
    message: "Route processed",
    data: {
      property_id: PROPERTY_ID,
      property_address:
        "123 Test Street, Pretoria",
      property_latitude: -25.7479,
      property_longitude: 28.2293,
      officer_latitude: -25.7600,
      officer_longitude: 28.2100,
      distance_metres: 2500,
      officer_location_updated_at:
        updatedAt,
      route_distance_metres:
        etaSeconds === null
          ? null
          : 3100,
      eta_seconds: etaSeconds,
      route_geometry:
        etaSeconds === null
          ? null
          : {
              type: "LineString",
              coordinates: [
                [28.2100, -25.7600],
                [28.2293, -25.7479],
              ],
            },
      routing_error: routingError,
    },
  };
}

function distanceResponse(
  updatedAt: string,
): AlertDistanceRes {
  return {
    status: 200,
    message: "Distance calculated",
    data: {
      property_id: PROPERTY_ID,
      property_address:
        "123 Test Street, Pretoria",
      property_latitude: -25.7479,
      property_longitude: 28.2293,
      officer_latitude: -25.7600,
      officer_longitude: 28.2100,
      distance_metres: 2500,
      officer_location_updated_at:
        updatedAt,
    },
  };
}

const mockFetchRoute =
  fetchAlertPropertyRoute as jest.MockedFunction<
    typeof fetchAlertPropertyRoute
  >;

const mockFetchDistance =
  fetchAlertPropertyDistance as jest.MockedFunction<
    typeof fetchAlertPropertyDistance
  >;

function triggerLocationCheck() {
  const intervalMock =
    window.setInterval as jest.MockedFunction<
      typeof window.setInterval
    >;

  const intervalCall =
    intervalMock.mock.calls.find(
      ([, delay]) => delay === 10_000,
    );

  if (!intervalCall) {
    throw new Error(
      "Location-check interval was not registered",
    );
  }

  const handler = intervalCall[0];

  if (typeof handler !== "function") {
    throw new TypeError(
      "Location-check handler is not callable",
    );
  }

  act(() => {
    handler();
  });
}

describe("useAlertPropertyRoute", () => {
  beforeEach(() => {
    jest.resetAllMocks();

    // This spy calls the real implementation. It only
    // records intervals so the polling callback can be
    // triggered without waiting ten seconds.
    jest.spyOn(window, "setInterval");
  });

  afterEach(() => {
    cleanup();
    jest.restoreAllMocks();
  });

  test("loads the initial route and ETA", async () => {
    mockFetchRoute.mockResolvedValue(
      routeResponse(
        FIRST_UPDATE,
        420,
      ),
    );

    const { result } = renderHook(() =>
      useAlertPropertyRoute(
        PROPERTY_ID,
        true,
      ),
    );

    await waitFor(() => {
      expect(
        result.current.route?.eta_seconds,
      ).toBe(420);
    });

    expect(
      result.current.route?.property_id,
    ).toBe(PROPERTY_ID);

    expect(
      result.current.routeError,
    ).toBeNull();

    expect(
      result.current.routeLoading,
    ).toBe(false);

    expect(
      mockFetchRoute,
    ).toHaveBeenCalledWith(PROPERTY_ID);
  });

  test(
    "recalculates ETA after officer location changes",
    async () => {
      mockFetchRoute
        .mockResolvedValueOnce(
          routeResponse(
            FIRST_UPDATE,
            420,
          ),
        )
        .mockResolvedValueOnce(
          routeResponse(
            SECOND_UPDATE,
            240,
          ),
        );

      mockFetchDistance.mockResolvedValue(
        distanceResponse(
          SECOND_UPDATE,
        ),
      );

      const { result } = renderHook(() =>
        useAlertPropertyRoute(
          PROPERTY_ID,
          true,
        ),
      );

      await waitFor(() => {
        expect(
          result.current.route?.eta_seconds,
        ).toBe(420);
      });

      triggerLocationCheck();

      await waitFor(() => {
        expect(
          mockFetchDistance,
        ).toHaveBeenCalledWith(
          PROPERTY_ID,
        );
      });

      await waitFor(() => {
        expect(
          result.current.route?.eta_seconds,
        ).toBe(240);
      });

      expect(
        result.current.route
          ?.officer_location_updated_at,
      ).toBe(SECOND_UPDATE);

      expect(
        mockFetchRoute,
      ).toHaveBeenCalledTimes(2);
    },
  );

  test(
    "does not recalculate when location is unchanged",
    async () => {
      mockFetchRoute.mockResolvedValue(
        routeResponse(
          FIRST_UPDATE,
          420,
        ),
      );

      mockFetchDistance.mockResolvedValue(
        distanceResponse(
          FIRST_UPDATE,
        ),
      );

      const { result } = renderHook(() =>
        useAlertPropertyRoute(
          PROPERTY_ID,
          true,
        ),
      );

      await waitFor(() => {
        expect(
          result.current.route?.eta_seconds,
        ).toBe(420);
      });

      triggerLocationCheck();

      await waitFor(() => {
        expect(
          mockFetchDistance,
        ).toHaveBeenCalledTimes(1);
      });

      expect(
        mockFetchRoute,
      ).toHaveBeenCalledTimes(1);

      expect(
        result.current.route?.eta_seconds,
      ).toBe(420);
    },
  );


});
