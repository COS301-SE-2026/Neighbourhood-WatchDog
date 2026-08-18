"use client";

import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import {
  AlertCard,
  type Alert,
  type AlertSeverity,
  type AlertStatus,
  getSeverity,
} from "@/components/shared/AlertCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SlidersHorizontal, RefreshCw, Wifi, WifiOff } from "lucide-react";
import {
  fetchAlerts,
  acknowledgeAlert,
  normaliseAlert,
  getAuthToken,
  WS_BASE,
  AlertFilters,
  broadcastAlert
} from "@/lib/api/alert";

const ALL_SEVERITIES: AlertSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const ALL_STATUSES: AlertStatus[] = ["NEW", "ACKNOWLEDGED", "RESOLVED"];
const CURRENT_CUTOFF = 24 * 60 * 60 * 1000; // 24h

const SEVERITY_LABELS: Record<AlertSeverity, string> = {
  CRITICAL: "Critical",
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
};

const STATUS_LABELS: Record<AlertStatus, string> = {
  NEW: "New",
  ACKNOWLEDGED: "Acknowledged",
  RESOLVED: "Resolved",
};

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center" role="status" aria-live="polite">
      <p className="text-base font-semibold" style={{ color: "var(--color-body)" }}>No alerts</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <p className="text-base font-semibold text-threat">Failed to load alerts</p>
      <p className="max-w-xs text-xs text-mist">{message}</p>
      <Button size="sm" variant="outline" onClick={onRetry} className="border-steel text-mist hover:bg-steel hover:text-white text-xs">
        Try again
      </Button>
    </div>
  );
}

function ActionErrorBanner({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <div role="alert" className="mb-4 flex items-center gap-2 rounded-lg border border-threat/30 bg-threat/10 px-4 py-3 text-sm text-threat">
      <span className="flex-1">{message}</span>
      <button type="button" onClick={onDismiss} aria-label="Dismiss error" className="ml-2 text-threat/60 transition-colors hover:text-threat">✕</button>
    </div>
  );
}

type FetchState = { alerts: Alert[]; loading: boolean; error: string | null };

type FetchAction =
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; payload: Alert[] }
  | { type: "FETCH_ERROR"; payload: string }
  | { type: "UPDATE_ALERT"; payload: Alert }
  | { type: "PREPEND_ALERT"; payload: Alert };

const initialFetchState: FetchState = { alerts: [], loading: true, error: null };

function fetchReducer(state: FetchState, action: FetchAction): FetchState {
  switch (action.type) {
    case "FETCH_START":
      return { ...state, loading: true, error: null };
    case "FETCH_SUCCESS":
      return { alerts: action.payload, loading: false, error: null };
    case "FETCH_ERROR":
      return { ...state, loading: false, error: action.payload };
    case "PREPEND_ALERT":
      if (state.alerts.some((alert) => alert.id === action.payload.id)) return state;
      return { ...state, alerts: [action.payload, ...state.alerts] };
    case "UPDATE_ALERT":
      return {
        ...state,
        alerts: state.alerts.map((alert) => (alert.id === action.payload.id ? action.payload : alert)),
      };
    default:
      return state;
  }
}

interface Props {
  neighbourhoodId: string;
}

export default function AlertsPage({ neighbourhoodId }: Props) {
  const [{ alerts, loading, error }, dispatch] = useReducer(fetchReducer, initialFetchState);

  const [actionError, setActionError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [fetchTick, setFetchTick] = useState(0);

  const [selectedSeverities, setSelectedSeverities] = useState<Set<AlertSeverity>>(new Set(ALL_SEVERITIES));
  const [selectedStatus, setSelectedStatus] = useState<AlertStatus | null>(null);
  const [activeTab, setActiveTab] = useState<"current" | "history">("current");
  const [historyStartDate, setHisoryStartDate] = useState("");
  const [historyEndDate, setHisoryEndDate] = useState("");
  const [broadcastingAlertId, setBroadcastingAlertId] = useState<string | null>(null);

  const alertFilters = useMemo<AlertFilters>(() => {
    const base: AlertFilters = {};
    if (selectedStatus) base.status = selectedStatus;
    if (activeTab === "history") {
      if (historyStartDate) base.startDate = new Date(historyStartDate);
      if (historyEndDate) base.endDate = new Date(historyEndDate);
    }
    return base;
  }, [activeTab, selectedStatus, historyStartDate, historyEndDate]);

  function triggerRefresh() {
    dispatch({ type: "FETCH_START" });
    setFetchTick((tick) => tick + 1);
  }

  const wsRef = useRef<WebSocket | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const filters: AlertFilters =
      activeTab === "current"
        ? { ...alertFilters, startDate: new Date(Date.now() - CURRENT_CUTOFF) }
        : alertFilters;

    fetchAlerts(neighbourhoodId, filters, controller.signal)
      .then(({ alerts: fetched }) => {
        if (!mountedRef.current) return;
        dispatch({ type: "FETCH_SUCCESS", payload: fetched });
      })
      .catch((err: unknown) => {
        if (!mountedRef.current) return;
        if (err instanceof DOMException && err.name === "AbortError") return;
        dispatch({ type: "FETCH_ERROR", payload: err instanceof Error ? err.message : "Unknown error" });
      });

    return () => controller.abort();
  }, [neighbourhoodId, fetchTick, alertFilters, activeTab]);

  useEffect(() => {
    if (activeTab !== "current") return;

    const token = getAuthToken();
    const url = `${WS_BASE}/alerts/${neighbourhoodId}/ws${token ? `?token=${token}` : ""}`;

    let unmounted = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      if (unmounted) return;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => { if (mountedRef.current) setWsConnected(true); };
      ws.onclose = () => {
        if (mountedRef.current) setWsConnected(false);
        if (!unmounted) reconnectTimer = setTimeout(connect, 3_000);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const message = JSON.parse(event.data as string) as { event: string; payload?: Record<string, unknown> };
          if (message.event === "ping") return;
          if (message.event === "alert.new" && message.payload) {
            dispatch({ type: "PREPEND_ALERT", payload: normaliseAlert(message.payload) });
          }
          if (message.event === "alert.acknowledged" && message.payload) {
            dispatch({ type: "UPDATE_ALERT", payload: normaliseAlert(message.payload) });
          }
        } catch {
          // Ignore malformed WebSocket payloads.
        }
      };
    }

    connect();

    return () => {
      unmounted = true;
      if (reconnectTimer !== null) clearTimeout(reconnectTimer);
      const ws = wsRef.current;
      if (ws) { ws.onclose = null; ws.close(); }
    };
  }, [neighbourhoodId, activeTab]);

  async function handleAcknowledge(id: string) {
    const original = alerts.find((alert) => alert.id === id);
    if (!original || original.status !== "NEW") return;

    setActionError(null);
    dispatch({ type: "UPDATE_ALERT", payload: { ...original, status: "ACKNOWLEDGED" } });

    try {
      await acknowledgeAlert(id);
    } catch (err) {
      if (mountedRef.current) {
        dispatch({ type: "UPDATE_ALERT", payload: original });
        setActionError(err instanceof Error ? err.message : "Failed to acknowledge alert.");
      }
      console.error("Acknowledge failed:", err);
    }
  }

  async function handleBroadcast(id: string) {
    const alert = alerts.find((item) => item.id === id);
    if (!alert || alert.status === "RESOLVED") return;

    setActionError(null);
    setBroadcastingAlertId(id);

    try {
      await broadcastAlert(id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to broadcast the alert.");
      console.error("Broadcast alert failed:", err);
    } finally {
      if (mountedRef.current) setBroadcastingAlertId(null);
    }
  }

  const filtered = useMemo(
    () => alerts.filter((alert) => selectedSeverities.has(getSeverity(alert.detection_type))),
    [alerts, selectedSeverities],
  );

  const hasActiveFilters =
    selectedSeverities.size < ALL_SEVERITIES.length ||
    selectedStatus !== null ||
    (activeTab === "history" && (historyStartDate !== "" || historyEndDate !== ""));

  const newCount = alerts.filter((alert) => alert.status === "NEW").length;
  const criticalCount = alerts.filter(
    (alert) => getSeverity(alert.detection_type) === "CRITICAL" && alert.status === "NEW",
  ).length;

  return (
    <TooltipProvider>
      <div className="w-full flex flex-col items-center px-8 py-10 bg-navy min-h-full font-sans">
        <div className="w-full max-w-2xl">
          <header className="mb-6 text-center">
            <div className="flex items-center justify-center gap-2">
              <h1 className="text-[2rem] font-bold leading-[2.5rem] text-white">Alerts</h1>
              <span title={wsConnected ? "Live updates connected" : "Live updates disconnected"} aria-label={wsConnected ? "Live" : "Offline"}>
                {wsConnected ? <Wifi className="h-4 w-4 text-safe mt-1" /> : <WifiOff className="h-4 w-4 text-mist/50 mt-1" />}
              </span>
            </div>

            {(newCount > 0 || criticalCount > 0) && (
              <div className="mt-3 flex flex-wrap justify-center gap-2" aria-live="polite">
                {newCount > 0 && (
                  <span
                    className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold"
                    style={{
                      backgroundColor: "color-mix(in srgb, var(--color-blue) 12%, transparent)",
                      border: "1px solid color-mix(in srgb, var(--color-blue) 25%, transparent)",
                      color: "var(--color-blue)",
                    }}
                  >
                    {newCount} new
                  </span>
                )}
                {criticalCount > 0 && (
                  <span
                    className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold"
                    style={{
                      backgroundColor: "color-mix(in srgb, var(--color-threat) 12%, transparent)",
                      border: "1px solid color-mix(in srgb, var(--color-threat) 25%, transparent)",
                      color: "var(--color-threat)",
                    }}
                  >
                    {criticalCount} critical
                  </span>
                )}
              </div>
            )}
          </header>

          {actionError && <ActionErrorBanner message={actionError} onDismiss={() => setActionError(null)} />}

          <div className="mb-4 flex justify-center gap-2" role="tablist">
            <Button role="tab" aria-selected={activeTab === "current"} size="sm" variant={activeTab === "current" ? "default" : "outline"} onClick={() => setActiveTab("current")} className="text-xs font-medium">
              Current
            </Button>
            <Button role="tab" aria-selected={activeTab === "history"} size="sm" variant={activeTab === "history" ? "default" : "outline"} onClick={() => setActiveTab("history")} className="text-xs font-medium">
              History
            </Button>
          </div>

          <Card className="bg-steel/40 border-steel rounded-xl">
            <div className="flex items-center justify-between gap-3 rounded-t-xl border-b border-steel px-5 py-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs font-medium transition-colors"
                    style={{
                      borderColor: hasActiveFilters ? "var(--color-blue)" : "var(--color-mist)",
                      backgroundColor: "transparent",
                      color: hasActiveFilters ? "var(--color-blue)" : "var(--color-body)",
                    }}
                    aria-label="Open filter options"
                  >
                    <SlidersHorizontal className="mr-1.5 h-3.5 w-3.5" />
                    Filter
                    {hasActiveFilters && (
                      <span className="ml-1.5 flex h-4 w-4 items-center justify-center rounded-full text-xs font-bold" style={{ backgroundColor: "var(--color-blue)", color: "var(--color-white)" }}>
                        !
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent align="start" className="w-52" style={{ backgroundColor: "var(--color-white)", borderColor: "var(--color-mist)", color: "var(--color-ink)" }}>
                  <DropdownMenuLabel className="text-xs uppercase tracking-wider" style={{ color: "var(--color-body)" }}>Severity</DropdownMenuLabel>
                  {ALL_SEVERITIES.map((severity) => (
                    <DropdownMenuCheckboxItem
                      key={severity}
                      className="cursor-pointer text-sm"
                      style={{ color: "var(--color-ink)" }}
                      checked={selectedSeverities.has(severity)}
                      onCheckedChange={(checked) => {
                        setSelectedSeverities((previous) => {
                          const next = new Set(previous);
                          if (checked) next.add(severity); else next.delete(severity);
                          return next;
                        });
                      }}
                    >
                      {SEVERITY_LABELS[severity]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  <DropdownMenuSeparator style={{ backgroundColor: "var(--color-mist)" }} />
                  <DropdownMenuLabel className="text-xs uppercase tracking-wider" style={{ color: "var(--color-body)" }}>Status</DropdownMenuLabel>
                  <DropdownMenuCheckboxItem className="cursor-pointer text-sm" style={{ color: "var(--color-ink)" }} checked={selectedStatus === null} onCheckedChange={() => setSelectedStatus(null)}>
                    All
                  </DropdownMenuCheckboxItem>
                  {ALL_STATUSES.map((status) => (
                    <DropdownMenuCheckboxItem key={status} className="cursor-pointer text-sm" style={{ color: "var(--color-ink)" }} checked={selectedStatus === status} onCheckedChange={(checked) => setSelectedStatus(checked ? status : null)}>
                      {STATUS_LABELS[status]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  {activeTab === "history" && (
                    <>
                      <DropdownMenuSeparator style={{ backgroundColor: "var(--color-mist)" }} />
                      <DropdownMenuLabel className="text-xs uppercase tracking-wider" style={{ color: "var(--color-body)" }}>Date range</DropdownMenuLabel>
                      <div className="flex flex-col gap-2 px-2 py-1.5">
                        <label className="text-xs" style={{ color: "var(--color-body)" }}>
                          From
                          <input type="date" value={historyStartDate} onChange={(event) => setHisoryStartDate(event.target.value)} className="mt-1 w-full rounded border px-2 py-1 text-xs" style={{ borderColor: "var(--color-mist)", color: "var(--color-ink)" }} />
                        </label>
                        <label className="text-xs" style={{ color: "var(--color-body)" }}>
                          To
                          <input type="date" value={historyEndDate} onChange={(event) => setHisoryEndDate(event.target.value)} className="mt-1 w-full rounded border px-2 py-1 text-xs" style={{ borderColor: "var(--color-mist)", color: "var(--color-ink)" }} />
                        </label>
                      </div>
                    </>
                  )}

                  {hasActiveFilters && (
                    <>
                      <DropdownMenuSeparator style={{ backgroundColor: "var(--color-mist)" }} />
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedSeverities(new Set(ALL_SEVERITIES));
                          setSelectedStatus(null);
                          setHisoryStartDate("");
                          setHisoryEndDate("");
                        }}
                        className="w-full px-2 py-1.5 text-left text-xs transition-colors"
                        style={{ color: "var(--color-blue)" }}
                        onMouseEnter={(event) => { event.currentTarget.style.color = "var(--color-navy)"; }}
                        onMouseLeave={(event) => { event.currentTarget.style.color = "var(--color-blue)"; }}
                      >
                        Clear all filters
                      </button>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              <Button variant="ghost" size="sm" onClick={triggerRefresh} disabled={loading} className="text-sky hover:text-white hover:bg-steel transition-colors text-xs" aria-label="Refresh alerts">
                <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>

            <section aria-label="Alert list" aria-live="polite" className="rounded-b-xl p-4">
              {loading && alerts.length === 0 ? (
                <div className="flex items-center justify-center py-20">
                  <RefreshCw className="h-5 w-5 animate-spin text-sky" />
                </div>
              ) : error ? (
                <ErrorState message={error} onRetry={() => setFetchTick((tick) => tick + 1)} />
              ) : filtered.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-3">
                  {filtered.map((alert) => (
                    <AlertCard key={alert.id} alert={alert} onAcknowledge={handleAcknowledge} onBroadcast={handleBroadcast} broadcasting={broadcastingAlertId === alert.id} />
                  ))}
                </div>
              )}
            </section>
          </Card>
        </div>
      </div>
    </TooltipProvider>
  );
}
