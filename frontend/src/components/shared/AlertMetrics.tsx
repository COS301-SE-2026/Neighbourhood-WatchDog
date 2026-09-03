"use client";
import React, { useState } from "react";
import { useAlertMetrics } from "@/hooks/use-alert-metrics";
import { Card } from "../ui/card";
import { RefreshCw } from "lucide-react";

interface AlertMetricsProps {
  readonly neighbourhoodId: string;
  readonly cameraOptions?: {
    id: string;
    name: string;
  }[];
  readonly officerOptions?: {
    id: string;
    name: string;
  }[];
}

function formatSeconds(seconds: number | null): string {
  if (seconds == null) return "-";
  if (seconds < 60) return `${Math.round(seconds)}s`;

  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);

  return `${mins}m ${secs}s`;
}

function StatusBadge({ status }: { status: string }) {
  const colours: Record<string, string> = {
    PENDING: "bg-brand-caution/15 text-brand-caution",
    ACKNOWLEDGED: "bg-brand-green/15 text-brand-green",
    RESOLVED: "bg-brand-pulse/15 text-brand-pulse",
  };

  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium ${colours[status] ?? "bg-brand-slate/15 text-brand-ash"}`}
    >
      {status}
    </span>
  );
}

export function AlertMetrics({
  neighbourhoodId,
  cameraOptions = [],
  officerOptions = [],
}: AlertMetricsProps) {
  const [cameraId, setCameraId] = useState<string | undefined>();
  const [officerId, setOfficerId] = useState<string | undefined>();

  const { metrics, loading, error, refetch } = useAlertMetrics(
    neighbourhoodId,
    cameraId,
    officerId,
  );

  return (
    <div className="space-y-4">
      {/* summary cards */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="p-4 bg-card border">
          <p className="text-xs text-muted-foreground mb-1">
            Average Response Time
          </p>
          <p className="text-2xl font-bold text-brand-frost">
            {loading
              ? "-"
              : formatSeconds(metrics?.average_response_seconds ?? null)}
          </p>
        </Card>
        <Card className="p-4 bg-card border">
          <p className="text-xs text-muted-foreground mb-1">Pending</p>
          <p className="text-2xl font-bold text-brand-caution">
            {loading ? "—" : (metrics?.pending_count ?? 0)}
          </p>
        </Card>
        <Card className="p-4 bg-card border">
          <p className="text-xs text-muted-foreground mb-1">Acknowledged</p>
          <p className="text-2xl font-bold text-brand-green">
            {loading ? "—" : (metrics?.acknowledged_count ?? 0)}
          </p>
        </Card>
      </div>

      {/* filters */}
      <div className="flex gap-3 items-center">
        {cameraOptions.length > 0 && (
          <select
            value={cameraId ?? ""}
            onChange={(e) => setCameraId(e.target.value || undefined)}
            className="bg-card border text-foreground text-xs rounded px-2 py-1"
          >
            <option value="">All cameras</option>
            {cameraOptions.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        )}
        {officerOptions.length > 0 && (
          <select
            value={officerId ?? ""}
            onChange={(e) => setOfficerId(e.target.value || undefined)}
            className="bg-card border text-foreground text-xs rounded px-2 py-1"
          >
            <option value="">All officers</option>
            {officerOptions.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        )}
        <button
          onClick={() => void refetch()}
          disabled={loading}
          className="ml-auto text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Refresh metrics"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`}
          />
        </button>
      </div>

      {/* per alert table */}
      {error ? (
        <p className="text-xs text-destructive">{error}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-foreground">
            <thead>
              <tr className="text-muted-foreground border-b">
                <th className="text-left py-2 pr-4">Camera</th>
                <th className="text-left py-2 pr-4">Created</th>
                <th className="text-left py-2 pr-4">Status</th>
                <th className="text-left py-2">Response Time</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan={4}
                    className="py-6 text-center text-muted-foreground"
                  >
                    Loading…
                  </td>
                </tr>
              ) : (metrics?.items ?? []).length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="py-6 text-center text-muted-foreground"
                  >
                    No alerts
                  </td>
                </tr>
              ) : (
                (metrics?.items ?? []).map((item) => (
                  <tr key={item.alert_id} className="border-b border-border/60">
                    <td className="py-2 pr-4 font-mono text-[10px] truncate max-w-30">
                      {item.camera_id.slice(0, 8)}…
                    </td>
                    <td className="py-2 pr-4">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="py-2 pr-4">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="py-2">
                      {formatSeconds(item.response_seconds)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
