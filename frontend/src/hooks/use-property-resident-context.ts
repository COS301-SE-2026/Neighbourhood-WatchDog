"use client";

import { useEffect, useState } from "react";
import {
  getPropertyResidentContext,
} from "@/lib/api/property";
import type {
  PropertyResidentContext,
} from "@/lib/validators/property";

export function usePropertyResidentContext(
  propertyId: string | null,
) {
  const [data, setData] =
    useState<PropertyResidentContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    if (!propertyId) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    void getPropertyResidentContext(propertyId)
      .then((result) => {
        if (!cancelled) {
          setData(result);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setError(
            "Resident information could not be loaded.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [propertyId, retryKey]);

  return {
    data,
    loading,
    error,
    retry: () => setRetryKey((value) => value + 1),
  };
}