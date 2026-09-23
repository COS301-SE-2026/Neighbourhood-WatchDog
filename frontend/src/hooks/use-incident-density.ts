import {
  useEffect,
  useState,
} from "react";

import { fetchIncidentDensity } from "@/lib/api/incident-density";
import type {
  IncidentDensityData,
  IncidentDensityViewport,
} from "@/lib/validators/incident-density";

const FETCH_DEBOUNCE_MS = 350;

interface UseIncidentDensityOptions {
  neighbourhoodId: string;
  startDate: string;
  endDate: string;
  viewport: IncidentDensityViewport | null;
  enabled: boolean;
}

interface UseIncidentDensityResult {
  data: IncidentDensityData | null;
  loading: boolean;
  error: string | null;
}

export function useIncidentDensity({
  neighbourhoodId,
  startDate,
  endDate,
  viewport,
  enabled,
}: UseIncidentDensityOptions): UseIncidentDensityResult {
  const [data, setData] = useState<IncidentDensityData | null>(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);


}
