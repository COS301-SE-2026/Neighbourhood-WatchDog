"use client";
import { useState, useEffect, useCallback } from "react";
import {
  fetchNeighbourhoodRiskScore,
  fetchNeighbourhoodRiskScoreHistory,
} from "@/lib/api/riskScore";
import { RiskScoreRes } from "@/lib/validators/riskScore";

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
