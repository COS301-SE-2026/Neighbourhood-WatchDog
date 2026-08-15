"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { AlertMetrics } from "@/components/shared/AlertMetrics";
// import { IncidentTrends } from "@/components/shared/IncidentTrends";
import { AlertFrequencyGraph } from "@/components/shared/AlertFrequencyGraph";
import { RiskScoreTrendGraph } from "@/components/shared/RiskScoreTrendGraph";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/api/alert";
import { useRiskScoreHistory } from "@/hooks/use-risk-score";

interface RiskScorePanelProps {
  readonly neighbourhoodId: string;
}

function AnalyticsLoadingState() {
  return (
    <div className="flex min-h-full w-full items-center justify-center bg-black px-6 py-10 text-sm text-white/50 md:px-8">
      <div className="flex items-center gap-2">
        <RefreshCw className="h-4 w-4 animate-spin text-emerald-400" />
        Resolving neighbourhood context...
      </div>
    </div>
  );
}

function RiskScorePanel({ neighbourhoodId }: RiskScorePanelProps) {
  const {
    riskHistory,
    loading,
    error,
  } = useRiskScoreHistory(neighbourhoodId, "minute");

  if (error) {
    return (
      <Card className="border border-red-500/20 bg-zinc-950 p-5 shadow-none">
        <p className="text-sm text-red-300">{error}</p>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="border border-white/10 bg-zinc-950 p-5 shadow-none">
        <p className="text-sm text-white/50">
          Loading risk-score history…
        </p>
      </Card>
    );
  }

  if (riskHistory.length === 0) {
    return (
      <Card className="border border-white/10 bg-zinc-950 p-5 shadow-none">
        <p className="text-sm text-white/50">
          No calculated risk-score history is available yet.
        </p>
      </Card>
    );
  }

  return <RiskScoreTrendGraph data={riskHistory} />;
}

function AnalyticsPageContent() {
  const searchParams = useSearchParams();

  const queryNeighbourhoodId =
    searchParams.get("neighbourhoodId") ||
    searchParams.get("neighbourhood_id");

  const [neighbourhoodId, setNeighbourhoodId] = useState<string | null>(null);
  const [identityLoading, setIdentityLoading] = useState(!queryNeighbourhoodId);
  const [identityError, setIdentityError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    if (queryNeighbourhoodId) {
      return;
    }

    let cancelled = false;

    fetchCurrentUser()
      .then((user) => {
        if (cancelled) return;

        if (user.neighbourhood_id) {
          setNeighbourhoodId(user.neighbourhood_id);
          setIdentityError(null);
        } else {
          setNeighbourhoodId(null);
          setIdentityError(
            "No neighbourhood is associated with the current user yet.",
          );
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;

        setNeighbourhoodId(null);
        setIdentityError(
          err instanceof Error ? err.message : "Failed to load current user.",
        );
      })
      .finally(() => {
        if (!cancelled) {
          setIdentityLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [queryNeighbourhoodId]);

  const resolvedNeighbourhoodId = queryNeighbourhoodId ?? neighbourhoodId;

  if (!queryNeighbourhoodId && identityLoading) {
    return <AnalyticsLoadingState />;
  }

  if (!resolvedNeighbourhoodId) {
    return (
      <div className="flex min-h-full w-full items-center justify-center bg-black px-6 py-10 text-center md:px-8">
        <Card className="max-w-md border border-white/10 bg-zinc-950 p-6 shadow-none">
          <p className="text-lg font-semibold text-white">
            Analytics need a neighbourhood
          </p>

          <p className="mt-2 text-sm leading-relaxed text-white/50">
            {identityError ||
              "Open this page with a neighbourhood ID, or sign in to a user that already belongs to one."}
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-full w-full bg-black px-6 py-7 text-white md:px-8">
      <div className="mx-auto w-full max-w-7xl">
        <header className="mb-7 flex flex-col gap-4 border-b border-white/10 pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-emerald-400">
              Neighbourhood management
            </p>

            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white">
              Analytics
            </h1>

            <p className="mt-2 text-sm text-white/50">
              Monitor alert activity, neighbourhood risk, and response trends.
            </p>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setRefreshTick((tick) => tick + 1)}
            className="w-fit text-white/55 hover:bg-white/5 hover:text-white"
            aria-label="Refresh analytics"
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            Refresh
          </Button>
        </header>

        {/* Trend charts */}
        <div className="mb-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
          <RiskScorePanel
            key={`risk-${refreshTick}`}
            neighbourhoodId={resolvedNeighbourhoodId}
          />

          <AlertFrequencyGraph
            key={`freq-${refreshTick}`}
            neighbourhoodId={resolvedNeighbourhoodId}
          />
        </div>

        {/* Response time metrics */}
        <Card className="mb-6 border border-white/10 bg-zinc-950 p-5 shadow-none">
          <div className="mb-5">
            <h2 className="text-base font-semibold text-white">
              Alert response metrics
            </h2>

            <p className="mt-1 text-sm text-white/45">
              Response activity for alerts in this neighbourhood.
            </p>
          </div>

          <AlertMetrics
            key={`metrics-${refreshTick}`}
            neighbourhoodId={resolvedNeighbourhoodId}
          />
        </Card>

        {/* Incident trend analysis */}
        {/* <Card className="mb-6 border border-white/10 bg-zinc-950 p-5 shadow-none">
          <div className="mb-5">
            <h2 className="text-base font-semibold text-white">
              Incident trends
            </h2>

            <p className="mt-1 text-sm text-white/45">
              Historical incident patterns for this neighbourhood.
            </p>
          </div>

          <IncidentTrends
            key={`incidents-${refreshTick}`}
            neighbourhoodId={neighbourhoodId}
          />
        </Card> */}
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <Suspense fallback={<AnalyticsLoadingState />}>
      <AnalyticsPageContent />
    </Suspense>
  );
}