"use client";

import { useEffect, useState } from "react";
import { getPropertyResidentContext } from "@/lib/api/property";
import type { PropertyResidentContext } from "@/lib/validators/property";

interface ResidentRequestKey {
  propertyId: string;
  retryKey: number;
}

export function usePropertyResidentContext(
  propertyId: string | null,
) {
  const [data, setData] =
    useState<PropertyResidentContext | null>(null);
  const [error, setError] =
    useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);
  const [completedRequest, setCompletedRequest] =
    useState<ResidentRequestKey | null>(null);

  useEffect(() => {
    if (!propertyId) {
      return;
    }

    let cancelled = false;

    void getPropertyResidentContext(propertyId)
      .then((result) => {
        if (cancelled) {
          return;
        }

        setData(result);
        setError(null);
        setCompletedRequest({
          propertyId,
          retryKey,
        });
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        setData(null);
        setError(
          "Resident information could not be loaded.",
        );
        setCompletedRequest({
          propertyId,
          retryKey,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [propertyId, retryKey]);

  const requestCompleted =
    propertyId !== null &&
    completedRequest?.propertyId === propertyId &&
    completedRequest.retryKey === retryKey;

  return {
    data: requestCompleted ? data : null,
    loading: propertyId !== null && !requestCompleted,
    error: requestCompleted ? error : null,
    retry: () => setRetryKey((value) => value + 1),
  };
}