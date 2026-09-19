"use client";

import { useEffect, useState } from "react";

import {
  fetchAlertPropertyDistance,
  fetchAlertPropertyRoute,
} from "@/lib/api/alert";
import type {
  AlertRouteData,
} from "@/lib/validators/alert";

const LOCATION_CHECK_INTERVAL_MS = 10_000;

interface RouteState {
  propertyId: string | null;
  data: AlertRouteData | null;
  error: string | null;
}

function routeErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    if (
      error.message.includes("unavailable") ||
      error.message.includes("stale") ||
      error.message.includes("422")
    ) {
      return (
        "Officer location is unavailable or stale."
      );
    }
  }

  return "Unable to calculate the route.";
}

export function useAlertPropertyRoute(
  propertyId: string | null,
  enabled: boolean,
) {
  const [state, setState] = useState<RouteState>({
    propertyId: null,
    data: null,
    error: null,
  });

  useEffect(() => {
    if (!enabled || !propertyId) {
      return;
    }

    let cancelled = false;
    let checkingLocation = false;
    let lastLocationUpdate: string | null = null;

    const loadRoute = async () => {
      try {
        const response =
          await fetchAlertPropertyRoute(
            propertyId,
          );

        if (cancelled) {
          return;
        }

        lastLocationUpdate =
          response.data
            .officer_location_updated_at;

        setState({
          propertyId,
          data: response.data,
          error: null,
        });
      } catch (error) {
        if (cancelled) {
          return;
        }

        setState({
          propertyId,
          data: null,
          error: routeErrorMessage(error),
        });
      }
    };

    const refreshWhenLocationChanges =
      async () => {
        if (checkingLocation) {
          return;
        }

        checkingLocation = true;

        try {
          const response =
            await fetchAlertPropertyDistance(
              propertyId,
            );

          const nextLocationUpdate =
            response.data
              .officer_location_updated_at;

          if (
            nextLocationUpdate !==
            lastLocationUpdate
          ) {
            await loadRoute();
          }
        } catch (error) {
          if (!cancelled) {
            setState({
              propertyId,
              data: null,
              error: routeErrorMessage(error),
            });
          }
        } finally {
          checkingLocation = false;
        }
      };

    void loadRoute();

    const intervalId = window.setInterval(
      () => {
        void refreshWhenLocationChanges();
      },
      LOCATION_CHECK_INTERVAL_MS,
    );

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [enabled, propertyId]);

  const active =
    enabled &&
    propertyId !== null &&
    state.propertyId === propertyId;

  return {
    route: active ? state.data : null,
    routeError: active ? state.error : null,
    routeLoading:
      enabled &&
      propertyId !== null &&
      !active,
  };
}
