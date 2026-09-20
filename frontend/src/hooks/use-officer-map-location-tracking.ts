"use client";

import { useEffect, useState } from "react";

import {
  getSecurityAvailability,
} from "@/lib/api/neighbourhood";
import {
  useOfficerLocationTracking,
} from "@/hooks/use-officer-location-tracking";

const AVAILABILITY_REFRESH_MS = 30_000;

export function useOfficerMapLocationTracking(
  neighbourhoodId: string,
  enabled: boolean,
) {
  const [onDuty, setOnDuty] = useState(false);

  useEffect(() => {
    if (!enabled || !neighbourhoodId) {
      return;
    }

    let cancelled = false;

    const refreshAvailability = async () => {
      try {
        const response =
          await getSecurityAvailability(
            neighbourhoodId,
          );

        if (cancelled) {
          return;
        }

        setOnDuty(
          response.availability === "AVAILABLE" ||
          response.availability === "BUSY",
        );
      } catch {
        if (!cancelled) {
          setOnDuty(false);
        }
      }
    };

    void refreshAvailability();

    const intervalId = window.setInterval(
      () => {
        void refreshAvailability();
      },
      AVAILABILITY_REFRESH_MS,
    );

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [enabled, neighbourhoodId]);

  useOfficerLocationTracking(
    neighbourhoodId,
    enabled && onDuty,
  );

  return { onDuty };
}
