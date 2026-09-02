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
import { useUserContext } from "@/hooks/use-user-context";
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
      <p className="text-base font-semibold text-white/45">No alerts</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <p className="text-base font-semibold text-red-400">Failed to load alerts</p>
      <p className="max-w-xs text-xs text-white/45">{message}</p>
      <Button size="sm" variant="outline" onClick={onRetry} className="border-white/10 bg-transparent text-white/70 hover:bg-white/5 hover:text-white text-xs">
        Try again
      </Button>
    </div>
  );
}

function ActionErrorBanner({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <div role="alert" className="mb-4 flex items-center gap-2 rounded-lg border border-red-400/30 bg-red-400/10 px-4 py-3 text-sm text-red-400">
      <span className="flex-1">{message}</span>
      <button type="button" onClick={onDismiss} aria-label="Dismiss error" className="ml-2 text-red-400/60 transition-colors hover:text-red-400">✕</button>
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

  const {
    data: userContext,
    isLoading: userContextLoading,
  } = useUserContext();

  const neighbourhoodRole = useMemo(
    () =>
      userContext?.properties.find(
        (property) =>
          property.neighbourhood?.id === neighbourhoodId,
      )?.neighbourhood?.role ?? null,
    [userContext, neighbourhoodId],
  );

  const isNeighbourhoodAdmin =
    neighbourhoodRole === "NEIGHBOURHOOD_ADMIN";

  const isSecurityOfficer =
    neighbourhoodRole === "SECURITY_OFFICER";

  const canViewAlerts =
    isNeighbourhoodAdmin || isSecurityOfficer;

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
    if (userContextLoading || !canViewAlerts) {
      return;
    }

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
  }, [neighbourhoodId, fetchTick, alertFilters, activeTab, userContextLoading, canViewAlerts]);

  useEffect(() => {
    if (activeTab !== "current" || userContextLoading || !canViewAlerts) return;

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
            const incomingAlert = normaliseAlert(message.payload);

            if (
              isSecurityOfficer &&
              getSeverity(incomingAlert.detection_type) !== "CRITICAL"
            ) {
              return;
            }

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
  }, [neighbourhoodId, activeTab, userContextLoading, canViewAlerts, isSecurityOfficer]);

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

  if (userContextLoading) {
    return (
      <main className="min-h-full bg-black px-6 py-8 text-white md:px-8">
        <div className="mx-auto flex max-w-6xl items-center justify-center py-20">
          <RefreshCw className="size-5 animate-spin text-emerald-400" />
        </div>
      </main>
    );
  }

  if (!canViewAlerts) {
    return (
      <main className="min-h-full bg-black px-6 py-8 text-white md:px-8">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm text-white/60">
            You do not have access to these alerts.
          </p>
        </div>
      </main>
    );
  }


  return (
    <TooltipProvider>
      <main className="min-h-full bg-black px-6 py-8 text-white md:px-8">
        <div className="w-full max-w-6xl">
          <header className="mb-7 border-b border-white/10 pb-6">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight text-white">{isNeighbourhoodAdmin ? "Live alerts" : "Critical alerts"}</h1>
              <span title={wsConnected ? "Live updates connected" : "Live updates disconnected"} aria-label={wsConnected ? "Live" : "Offline"}>
                {wsConnected ? <Wifi className="h-4 w-4 text-emerald-400 mt-1" /> : <WifiOff className="h-4 w-4 text-white/30 mt-1" />}
              </span>
            </div>

            <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/50">
              {isNeighbourhoodAdmin
                ? "Monitor alerts across your neighbourhood and broadcast incidents when needed."
                : "Review critical events that require a security response."}
            </p>


            {(newCount > 0 || criticalCount > 0) && (
              <div className="mt-3 flex flex-wrap justify-center gap-2" aria-live="polite">
                {newCount > 0 && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
                    {newCount} new
                  </span>
                )}
                {criticalCount > 0 && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-red-400/25 bg-red-400/10 px-3 py-1 text-xs font-semibold text-red-400">
                    {criticalCount} critical
                  </span>
                )}
              </div>
            )}
          </header>

          {actionError && <ActionErrorBanner message={actionError} onDismiss={() => setActionError(null)} />}

          <div className="mb-5 flex gap-2" role="tablist">
            <Button role="tab" aria-selected={activeTab === "current"} size="sm" variant={activeTab === "current" ? "default" : "outline"} onClick={() => setActiveTab("current")} className={activeTab === "current" ? "bg-emerald-500 text-black hover:bg-emerald-400 text-xs font-medium" : "border-white/10 bg-transparent text-white/70 hover:bg-white/5 hover:text-white text-xs font-medium"}>
              Current
            </Button>
            <Button role="tab" aria-selected={activeTab === "history"} size="sm" variant={activeTab === "history" ? "default" : "outline"} onClick={() => setActiveTab("history")} className={activeTab === "history" ? "bg-emerald-500 text-black hover:bg-emerald-400 text-xs font-medium" : "border-white/10 bg-transparent text-white/70 hover:bg-white/5 hover:text-white text-xs font-medium"}>
              History
            </Button>
          </div>

          <Card className="overflow-hidden rounded-lg border border-white/10 bg-[#101011]">
            <div className="flex items-center justify-between gap-3 rounded-t-xl border-b border-white/10 px-5 py-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className={`text-xs font-medium transition-colors bg-transparent ${hasActiveFilters ? "border-emerald-400 text-emerald-400" : "border-white/10 text-white/45"}`}
                    aria-label="Open filter options"
                  >
                    <SlidersHorizontal className="mr-1.5 h-3.5 w-3.5" />
                    Filter
                    {hasActiveFilters && (
                      <span className="ml-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-400 text-xs font-bold text-black">
                        !
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent align="start" className="w-52 border-white/10 bg-zinc-950 text-white">
                  <DropdownMenuLabel className="text-xs uppercase tracking-wider text-white/45">Severity</DropdownMenuLabel>
                  {ALL_SEVERITIES.map((severity) => (
                    <DropdownMenuCheckboxItem
                      key={severity}
                      className="cursor-pointer text-sm text-white/80 focus:bg-white/5 focus:text-white"
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

                  <DropdownMenuSeparator className="bg-white/10" />
                  <DropdownMenuLabel className="text-xs uppercase tracking-wider text-white/45">Status</DropdownMenuLabel>
                  <DropdownMenuCheckboxItem className="cursor-pointer text-sm text-white/80 focus:bg-white/5 focus:text-white" checked={selectedStatus === null} onCheckedChange={() => setSelectedStatus(null)}>
                    All
                  </DropdownMenuCheckboxItem>
                  {ALL_STATUSES.map((status) => (
                    <DropdownMenuCheckboxItem key={status} className="cursor-pointer text-sm text-white/80 focus:bg-white/5 focus:text-white" checked={selectedStatus === status} onCheckedChange={(checked) => setSelectedStatus(checked ? status : null)}>
                      {STATUS_LABELS[status]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  {activeTab === "history" && (
                    <>
                      <DropdownMenuSeparator className="bg-white/10" />
                      <DropdownMenuLabel className="text-xs uppercase tracking-wider text-white/45">Date range</DropdownMenuLabel>
                      <div className="flex flex-col gap-2 px-2 py-1.5">
                        <label className="text-xs text-white/45">
                          From
                          <input type="date" value={historyStartDate} onChange={(event) => setHisoryStartDate(event.target.value)} className="mt-1 w-full rounded border border-white/10 bg-zinc-950 px-2 py-1 text-xs text-white" />
                        </label>
                        <label className="text-xs text-white/45">
                          To
                          <input type="date" value={historyEndDate} onChange={(event) => setHisoryEndDate(event.target.value)} className="mt-1 w-full rounded border border-white/10 bg-zinc-950 px-2 py-1 text-xs text-white" />
                        </label>
                      </div>
                    </>
                  )}

                  {hasActiveFilters && (
                    <>
                      <DropdownMenuSeparator className="bg-white/10" />
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedSeverities(new Set(ALL_SEVERITIES));
                          setSelectedStatus(null);
                          setHisoryStartDate("");
                          setHisoryEndDate("");
                        }}
                        className="w-full px-2 py-1.5 text-left text-xs text-emerald-400 transition-colors hover:text-emerald-300"
                      >
                        Clear all filters
                      </button>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              <Button variant="ghost" size="sm" onClick={triggerRefresh} disabled={loading} className="text-emerald-400 hover:text-white hover:bg-white/5 transition-colors text-xs" aria-label="Refresh alerts">
                <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>

            <section
              aria-label="Alert list"
              aria-live="polite"
              className="rounded-b-lg p-5 md:p-6"
            >

              {loading && alerts.length === 0 ? (
                <div className="flex items-center justify-center py-20">
                  <RefreshCw className="h-5 w-5 animate-spin text-emerald-400" />
                </div>
              ) : error ? (
                <ErrorState message={error} onRetry={() => setFetchTick((tick) => tick + 1)} />
              ) : filtered.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-3">
                  {filtered.map((alert) => (
                    <AlertCard key={alert.id} alert={alert} onAcknowledge={handleAcknowledge} onBroadcast={isNeighbourhoodAdmin ? handleBroadcast : undefined} broadcasting={broadcastingAlertId === alert.id} />
                  ))}
                </div>
              )}
            </section>
          </Card>
        </div>
      </main>
    </TooltipProvider>
  );
}
