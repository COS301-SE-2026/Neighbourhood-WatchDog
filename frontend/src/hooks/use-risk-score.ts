"use client";
import { useState, useEffect, useCallback } from "react";
import {
  fetchNeighbourhoodRiskScore,
  fetchNeighbourhoodRiskScoreHistory,
} from "@/lib/api/riskScore";
import {
  Granularities,
  RiskLevel,
  RiskScoreRes,
} from "@/lib/validators/riskScore";

export function useRiskScore(neighbourhoodId: string) {
  const [risk, setRisk] = useState<RiskScoreRes | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRiskScore = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetchNeighbourhoodRiskScore(neighbourhoodId);
      setRisk(res.data ?? null);
    } catch (e) {
      setError(`Failed to load risk score: ${e}`);
    } finally {
      setLoading(false);
    }
  }, [neighbourhoodId]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      void fetchRiskScore();
    }, 0);

    return () => clearTimeout(timeoutId);
  }, [fetchRiskScore]);

  return {
    risk,
    loading,
    error,
    refetch: fetchRiskScore,
  };
}

export function useRiskScoreHistory(
  neighbourhoodId: string,
  granularity: Granularities,
  start?: string,
  end?: string,
) {
  const [riskHistory, setRiskHistory] = useState<RiskScoreRes[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRiskScoreHistory = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetchNeighbourhoodRiskScoreHistory(
        neighbourhoodId,
        granularity,
        start,
        end,
      );
      setRiskHistory(res.data);
    } catch (e) {
      setError(`Failed to load risk score history: ${e}`);
    } finally {
      setLoading(false);
    }
  }, [neighbourhoodId, granularity, start, end]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      void fetchRiskScoreHistory();
    }, 0);

    return () => clearTimeout(timeoutId);
  }, [fetchRiskScoreHistory]);

  return {
    riskHistory,
    loading,
    error,
    refetch: fetchRiskScoreHistory,
  };
}
