"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getNeighbourhoodMapProperties,
} from "@/lib/api/neighbourhood";

import type {
  NeighbourhoodMapProperty,
} from "@/lib/validators/neighbourhood";

interface UseNeighbourhoodMapPropertiesResult {
  readonly properties: NeighbourhoodMapProperty[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly retry: () => Promise<unknown>;
}

export function useNeighbourhoodMapProperties(
  neighbourhoodId: string,
  enabled: boolean,
): UseNeighbourhoodMapPropertiesResult {
  const query = useQuery({
    queryKey: [
      "neighbourhood-map-properties",
      neighbourhoodId,
    ],
    queryFn: () =>
      getNeighbourhoodMapProperties(
        neighbourhoodId,
      ),
    enabled:
      enabled &&
      Boolean(neighbourhoodId),
    staleTime: 60_000,
  });

  return {
    properties: query.data ?? [],
    loading: query.isLoading,
    error:
      query.error instanceof Error
        ? query.error.message
        : query.error
          ? "Unable to load neighbourhood properties"
          : null,
    retry: query.refetch,
  };
}