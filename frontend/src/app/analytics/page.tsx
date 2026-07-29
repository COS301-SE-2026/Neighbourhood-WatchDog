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
    <div className="w-full min-h-full flex items-center justify-center px-8 py-10 bg-navy text-mist">
      <div className="flex items-center gap-2">
        <RefreshCw className="h-4 w-4 animate-spin text-sky" />
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
      <Card className="bg-card border rounded-xl p-6">
        <p className="text-sm text-destructive">{error}</p>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="bg-card border rounded-xl p-6">
        <p className="text-sm text-muted-foreground">
          Loading risk-score history…
        </p>
      </Card>
    );
  }

  if (riskHistory.length === 0) {
    return (
      <Card className="bg-card border rounded-xl p-6">
        <p className="text-sm text-muted-foreground">
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

  const [neighbourhoodId, setNeighbourhoodId] = useState<string | null>(
    queryNeighbourhoodId,
  );
  const [identityLoading, setIdentityLoading] = useState(
    !queryNeighbourhoodId,
  );
  const [identityError, setIdentityError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    if (queryNeighbourhoodId) {
      setNeighbourhoodId(queryNeighbourhoodId);
      setIdentityError(null);
      setIdentityLoading(false);
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

  if (identityLoading) {
    return <AnalyticsLoadingState />;
  }

  if (!neighbourhoodId) {
    return (
      <div className="w-full min-h-full flex items-center justify-center px-8 py-10 bg-navy text-center">
        <Card className="max-w-md bg-steel/40 border-steel rounded-xl p-6 text-white">
          <p className="text-lg font-semibold">
            Analytics need a neighbourhood
          </p>

          <p className="mt-2 text-sm text-mist">
            {identityError ||
              "Open this page with a neighbourhood ID, or sign in to a user that already belongs to one."}
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col items-center px-8 py-10 bg-navy min-h-full font-sans">
      <div className="w-full max-w-6xl">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-[2rem] font-bold leading-10 text-white">
              Analytics
            </h1>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setRefreshTick((tick) => tick + 1)}
            className="text-sky hover:text-white hover:bg-steel transition-colors text-xs"
            aria-label="Refresh analytics"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Refresh
          </Button>
        </header>

        {/* Trend charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <RiskScorePanel
            key={`risk-${refreshTick}`}
            neighbourhoodId={neighbourhoodId}
          />

          <AlertFrequencyGraph
            key={`freq-${refreshTick}`}
            neighbourhoodId={neighbourhoodId}
          />
        </div>

        {/* Response time metrics */}
        <Card
          className="bg-card border rounded-xl p-6 mb-6"
          style={{
            borderColor: "var(--border)",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <h2
            className="text-base font-bold mb-4"
            style={{ color: "var(--color-navy)" }}
          >
            Alert Response Metrics
          </h2>

          <AlertMetrics
            key={`metrics-${refreshTick}`}
            neighbourhoodId={neighbourhoodId}
          />
        </Card>

        {/* Incident trend analysis */}
        {/* <Card
          className="bg-card border rounded-xl p-6 mb-6"
          style={{
            borderColor: "var(--border)",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <h2
            className="text-base font-bold mb-4"
            style={{ color: "var(--color-navy)" }}
          >
            Incident Trends
          </h2>

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