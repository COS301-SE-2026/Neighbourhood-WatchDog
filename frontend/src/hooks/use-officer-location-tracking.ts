"use client";

import { useEffect } from "react";
import { Geolocation } from "@capacitor/geolocation";

import {
  updateSecurityLocation,
} from "@/lib/api/neighbourhood";

const LOCATION_WATCH_INTERVAL_MS = 10_000;

export function useOfficerLocationTracking(
  neighbourhoodId: string,
  onDuty: boolean,
) {
  useEffect(() => {
    if (!onDuty || !neighbourhoodId) {
      return;
    }

    let watchId: string | null = null;
    let stopped = false;
    let updateInProgress = false;

    const startWatching = async () => {
      try {
        const id =
          await Geolocation.watchPosition(
            {
              enableHighAccuracy: true,
              timeout: 15_000,
              maximumAge: 5_000,
              minimumUpdateInterval:
                LOCATION_WATCH_INTERVAL_MS,
              interval:
                LOCATION_WATCH_INTERVAL_MS,
            },
            (position, error) => {
              if (
                stopped ||
                updateInProgress
              ) {
                return;
              }

              if (error || !position) {
                console.error(
                  "Officer location watch failed",
                  error,
                );
                return;
              }

              updateInProgress = true;

              void updateSecurityLocation({
                neighbourhood_id:
                  neighbourhoodId,
                latitude:
                  position.coords.latitude,
                longitude:
                  position.coords.longitude,
              })
                .catch((updateError) => {
                  console.error(
                    "Failed to update officer location",
                    updateError,
                  );
                })
                .finally(() => {
                  updateInProgress = false;
                });
            },
          );

        if (stopped) {
          await Geolocation.clearWatch({
            id,
          });
          return;
        }

        watchId = id;
      } catch (error) {
        console.error(
          "Failed to start officer location tracking",
          error,
        );
      }
    };

    void startWatching();

    return () => {
      stopped = true;

      if (watchId) {
        void Geolocation.clearWatch({
          id: watchId,
        });
      }
    };
  }, [neighbourhoodId, onDuty]);
}
