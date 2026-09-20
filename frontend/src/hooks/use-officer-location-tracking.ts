"use client";

import { useEffect } from "react";

import { useLocationPermission } from "./use-location-permission";
import {
  updateSecurityLocation,
} from "@/lib/api/neighbourhood";
import { BackgroundGeolocation } from "@capgo/background-geolocation";

export function useOfficerLocationTracking(
  neighbourhoodId: string,
  onDuty: boolean,
) {
  const { backgroundStatus, requestBackground } = useLocationPermission();

  useEffect(() => {
    if (!onDuty || !neighbourhoodId) {
      return;
    }

    let stopped = false;
    let updateInProgress = false;

    const startWatching = async () => {
      if (backgroundStatus !== "granted"){
        await requestBackground();
      }
      
      try {
        await BackgroundGeolocation.start(
          {
            backgroundMessage: "WatchDog is sharing your location while on duty.",
            backgroundTitle: "On duty. Sharing location",
            requestPermissions: false,
            distanceFilter: 0,
          },
          (location, error) => {
            if (stopped || updateInProgress) {
              return;
            }

            if (error || !location) {
              console.error("Officer location watch failed", error);
              return;
            }

            updateInProgress = true;

            void updateSecurityLocation({
              neighbourhood_id: neighbourhoodId,
              latitude: location.latitude,
              longitude: location.longitude,
            })
              .catch((updateError) => {
                console.error("Failed to update officer location",updateError);
              })
              .finally(() => {
                updateInProgress = false;
              });
          },
        );
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

      void BackgroundGeolocation.stop();
    };
  }, [neighbourhoodId, onDuty, backgroundStatus, requestBackground]);
}
