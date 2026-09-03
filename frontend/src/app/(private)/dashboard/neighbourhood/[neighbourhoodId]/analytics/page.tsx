"use client";

import {useState } from "react";
import { useParams } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { AlertMetrics } from "@/components/shared/AlertMetrics";
// import { IncidentTrends } from "@/components/shared/IncidentTrends";
import { AlertFrequencyGraph } from "@/components/shared/AlertFrequencyGraph";
import { RiskScoreTrendGraph } from "@/components/shared/RiskScoreTrendGraph";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useRiskScoreHistory } from "@/hooks/use-risk-score";

interface RiskScorePanelProps {
  readonly neighbourhoodId: string;
}

function AnalyticsLoadingState() {
  return (
    <div className="flex min-h-full w-full items-center justify-center bg-brand-void px-6 py-10 text-sm text-brand-ash md:px-8">
      <div className="flex items-center gap-2">
        <RefreshCw className="h-4 w-4 animate-spin text-brand-green" />
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
      <Card className="border border-brand-threat/20 bg-brand-abyss p-5 shadow-none">
        <p className="text-sm text-brand-threat">{error}</p>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="border border-border bg-brand-abyss p-5 shadow-none">
        <p className="text-sm text-brand-ash">
          Loading risk-score history…
        </p>
      </Card>
    );
  }

  if (riskHistory.length === 0) {
    return (
      <Card className="border border-border bg-brand-abyss p-5 shadow-none">
        <p className="text-sm text-brand-ash">
          No calculated risk-score history is available yet.
        </p>
      </Card>
    );
  }

  return <RiskScoreTrendGraph data={riskHistory} />;
}

export default function AnalyticsPage() {

  const { neighbourhoodId } = useParams<{ neighbourhoodId: string}>();
  const [refreshTick, setRefreshTick] = useState(0);

  return (
    <div>
      <div>
        <header className="mb-7 flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-brand-green">
              Neighbourhood management
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-brand-frost">Analytics</h1>
            <p className="mt-2 text-sm text-brand-ash">
              Monitor alert activity, neighbourhood risk, and response trends.
            </p>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setRefreshTick((tick) => tick + 1)}
            className="w-fit text-brand-ash hover:bg-brand-slate hover:text-brand-frost"
            aria-label="Refresh analytics"
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            Refresh
          </Button>
        </header>

        <div className="mb-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
          <RiskScorePanel key={`risk-${refreshTick}`} neighbourhoodId={neighbourhoodId} />
          <AlertFrequencyGraph key={`freq-${refreshTick}`} neighbourhoodId={neighbourhoodId} />
        </div>


        <Card className="mb-6 border border-border bg-brand-abyss p-5 shadow-none">
          <div className="mb-5">
            <h2 className="text-base font-semibold text-brand-frost">Alert response metrics</h2>
            <p className="mt-1 text-sm text-brand-ash">Response activity for alerts in this neighbourhood.</p>
          </div>
          <AlertMetrics key={`metrics-${refreshTick}`} neighbourhoodId={neighbourhoodId} />
        </Card>

      </div>
    </div>
  );
}