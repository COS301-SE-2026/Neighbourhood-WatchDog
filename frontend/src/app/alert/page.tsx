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
} from "@/lib/api/alert";

const ALL_SEVERITIES: AlertSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const ALL_STATUSES: AlertStatus[] = ["NEW", "ACKNOWLEDGED", "RESOLVED"];

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
    <div
      className="flex flex-col items-center justify-center py-20 text-center"
      role="status"
      aria-live="polite"
    >
      <p className="text-[15px] font-semibold text-white/60">No alerts</p>
    </div>
  );
}

function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
      <p className="text-[15px] font-semibold text-red-400">
        Failed to load alerts
      </p>
      <p className="text-xs text-white/40 max-w-xs">{message}</p>
      <Button
        size="sm"
        variant="outline"
        onClick={onRetry}
        className="border-[#2C3E6B] text-[#D0D7E8] hover:bg-[#2C3E6B] hover:text-white text-xs"
      >
        Try again
      </Button>
    </div>
  );
}

type FetchState = {
  alerts: Alert[];
  loading: boolean;
  error: string | null;
};

type FetchAction =
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; payload: Alert[] }
  | { type: "FETCH_ERROR"; payload: string }
  | { type: "UPDATE_ALERT"; payload: Alert }
  | { type: "PREPEND_ALERT"; payload: Alert };

const initialFetchState: FetchState = {
  alerts: [],
  loading: true,
  error: null,
};

function fetchReducer(state: FetchState, action: FetchAction): FetchState {
  switch (action.type) {
    case "FETCH_START":
      return { ...state, loading: true, error: null };
    case "FETCH_SUCCESS":
      return { alerts: action.payload, loading: false, error: null };
    case "FETCH_ERROR":
      return { ...state, loading: false, error: action.payload };
    case "PREPEND_ALERT":
      if (state.alerts.some((a) => a.id === action.payload.id)) return state;
      return { ...state, alerts: [action.payload, ...state.alerts] };
    case "UPDATE_ALERT":
      return {
        ...state,
        alerts: state.alerts.map((a) =>
          a.id === action.payload.id ? action.payload : a,
        ),
      };
  }
}
interface Props {
  neighbourhoodId: string;
}

export default function AlertsPage({ neighbourhoodId }: Props) {
  const [{ alerts, loading, error }, dispatch] = useReducer(
    fetchReducer,
    initialFetchState,
  );
  const [wsConnected, setWsConnected] = useState(false);

  const [fetchTick, setFetchTick] = useState(0);

  const [selectedSeverities, setSelectedSeverities] = useState<
    Set<AlertSeverity>
  >(new Set(ALL_SEVERITIES));
  const [selectedStatuses, setSelectedStatuses] = useState<Set<AlertStatus>>(
    new Set(["NEW", "ACKNOWLEDGED"]),
  );

  function triggerRefresh() {
    dispatch({ type: "FETCH_START" });
    setFetchTick((t) => t + 1);
  }

  const wsRef = useRef<WebSocket | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    fetchAlerts(neighbourhoodId, controller.signal)
      .then((data) => {
        if (!mountedRef.current) return;
        dispatch({ type: "FETCH_SUCCESS", payload: data });
      })
      .catch((err: unknown) => {
        if (!mountedRef.current) return;
        if (err instanceof DOMException && err.name === "AbortError") return;
        dispatch({
          type: "FETCH_ERROR",
          payload: err instanceof Error ? err.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, [neighbourhoodId, fetchTick]);

  useEffect(() => {
    const token = getAuthToken();
    const url = `${WS_BASE}/alerts/${neighbourhoodId}/ws${token ? `?token=${token}` : ""}`;
    let unmounted = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      if (unmounted) return;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (mountedRef.current) setWsConnected(true);
      };

      ws.onclose = () => {
        if (mountedRef.current) setWsConnected(false);
        if (!unmounted) {
          reconnectTimer = setTimeout(connect, 3_000);
        }
      };

      ws.onerror = () => ws.close();

      ws.onmessage = (e) => {
        if (!mountedRef.current) return;
        try {
          const msg = JSON.parse(e.data as string) as {
            event: string;
            payload?: Record<string, unknown>;
          };

          if (msg.event === "ping") return;

          if (msg.event === "alert.new" && msg.payload) {
            dispatch({
              type: "PREPEND_ALERT",
              payload: normaliseAlert(msg.payload),
            });
          }

          if (msg.event === "alert.acknowledged" && msg.payload) {
            dispatch({
              type: "UPDATE_ALERT",
              payload: normaliseAlert(msg.payload),
            });
          }
        } catch {
          // Ignore
        }
      };
    }

    connect();

    return () => {
      unmounted = true;
      if (reconnectTimer !== null) clearTimeout(reconnectTimer);
      const ws = wsRef.current;
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
    };
  }, [neighbourhoodId]);

  async function handleAcknowledge(id: string) {
    const original = alerts.find((a) => a.id === id);
    if (!original) return;

    dispatch({
      type: "UPDATE_ALERT",
      payload: { ...original, status: "ACKNOWLEDGED" },
    });

    try {
      await acknowledgeAlert(id);
    } catch (err) {
      if (mountedRef.current) {
        dispatch({ type: "UPDATE_ALERT", payload: original });
      }
      console.error("Acknowledge failed:", err);
    }
  }

  const filtered = useMemo(
    () =>
      alerts.filter((a) => {
        const sev = getSeverity(a.detection_type);
        return (
          selectedSeverities.has(sev) &&
          selectedStatuses.has(a.status as AlertStatus)
        );
      }),
    [alerts, selectedSeverities, selectedStatuses],
  );

  const hasActiveFilters =
    selectedSeverities.size < ALL_SEVERITIES.length ||
    !selectedStatuses.has("NEW") ||
    !selectedStatuses.has("ACKNOWLEDGED") ||
    selectedStatuses.has("RESOLVED");

  const newCount = alerts.filter((a) => a.status === "NEW").length;
  const criticalCount = alerts.filter(
    (a) => getSeverity(a.detection_type) === "CRITICAL" && a.status === "NEW",
  ).length;

  return (
    <TooltipProvider>
      <div
        className="w-full flex flex-col items-center px-8 py-10 bg-[#1D2A5E] min-h-full"
        style={{
          fontFamily: "var(--font-sans, 'Inter', system-ui, sans-serif)",
        }}
      >
        <div className="w-full max-w-2xl">
          <header className="mb-6 text-center">
            <div className="flex items-center justify-center gap-2">
              <h1 className="text-[32px] font-bold leading-10 text-white">
                Alerts
              </h1>
              <span
                title={
                  wsConnected
                    ? "Live updates connected"
                    : "Live updates disconnected"
                }
                aria-label={wsConnected ? "Live" : "Offline"}
              >
                {wsConnected ? (
                  <Wifi className="h-4 w-4 text-[#16A34A] mt-1" />
                ) : (
                  <WifiOff className="h-4 w-4 text-white/30 mt-1" />
                )}
              </span>
            </div>

            {(newCount > 0 || criticalCount > 0) && (
              <div
                className="flex gap-2 mt-3 flex-wrap justify-center"
                aria-live="polite"
              >
                {newCount > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold bg-[#3B5EDE]/20 border border-[#3B5EDE]/30 rounded-full px-3 py-1 text-[#5B8DEF]">
                    {newCount} new
                  </span>
                )}
                {criticalCount > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold bg-[#DC2626]/20 border border-[#DC2626]/30 rounded-full px-3 py-1 text-[#DC2626]">
                    {criticalCount} critical
                  </span>
                )}
              </div>
            )}
          </header>

          <Card className="bg-[#2C3E6B]/40 border-[#2C3E6B] rounded-2xl">
            {/* Toolbar */}
            <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-[#2C3E6B] rounded-t-2xl">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className={[
                      "border-[#2C3E6B] bg-transparent text-[#D0D7E8] hover:bg-[#2C3E6B] hover:text-white transition-colors text-xs font-medium",
                      hasActiveFilters
                        ? "border-[#3B5EDE]/60 text-[#5B8DEF]"
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    aria-label="Open filter options"
                  >
                    <SlidersHorizontal className="h-3.5 w-3.5 mr-1.5" />
                    Filter
                    {hasActiveFilters && (
                      <span className="ml-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#3B5EDE] text-[9px] font-bold text-white">
                        !
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="start"
                  className="w-52 bg-[#1D2A5E] border-[#2C3E6B] text-white"
                >
                  <DropdownMenuLabel className="text-[#D0D7E8]/60 text-[10px] uppercase tracking-wider">
                    Severity
                  </DropdownMenuLabel>
                  {ALL_SEVERITIES.map((sev) => (
                    <DropdownMenuCheckboxItem
                      key={sev}
                      className="text-sm text-white focus:bg-[#2C3E6B] focus:text-white cursor-pointer"
                      checked={selectedSeverities.has(sev)}
                      onCheckedChange={(checked) => {
                        setSelectedSeverities((prev) => {
                          const next = new Set(prev);
                          checked ? next.add(sev) : next.delete(sev);
                          return next;
                        });
                      }}
                    >
                      {SEVERITY_LABELS[sev]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  <DropdownMenuSeparator className="bg-[#2C3E6B]" />

                  <DropdownMenuLabel className="text-[#D0D7E8]/60 text-[10px] uppercase tracking-wider">
                    Status
                  </DropdownMenuLabel>
                  {ALL_STATUSES.map((st) => (
                    <DropdownMenuCheckboxItem
                      key={st}
                      className="text-sm text-white focus:bg-[#2C3E6B] focus:text-white cursor-pointer"
                      checked={selectedStatuses.has(st)}
                      onCheckedChange={(checked) => {
                        setSelectedStatuses((prev) => {
                          const next = new Set(prev);
                          checked ? next.add(st) : next.delete(st);
                          return next;
                        });
                      }}
                    >
                      {STATUS_LABELS[st]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  {hasActiveFilters && (
                    <>
                      <DropdownMenuSeparator className="bg-[#2C3E6B]" />
                      <button
                        onClick={() => {
                          setSelectedSeverities(new Set(ALL_SEVERITIES));
                          setSelectedStatuses(new Set(["NEW", "ACKNOWLEDGED"]));
                        }}
                        className="w-full text-left px-2 py-1.5 text-xs text-[#5B8DEF] hover:text-white transition-colors"
                      >
                        Clear all filters
                      </button>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              <Button
                variant="ghost"
                size="sm"
                onClick={triggerRefresh}
                disabled={loading}
                className="text-[#5B8DEF] hover:text-white hover:bg-[#2C3E6B] transition-colors text-xs"
                aria-label="Refresh alerts"
              >
                <RefreshCw
                  className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
            </div>

            {/* Alert list */}
            <section
              aria-label="Alert list"
              aria-live="polite"
              className="p-4 rounded-b-2xl"
            >
              {loading && alerts.length === 0 ? (
                <div className="flex items-center justify-center py-20">
                  <RefreshCw className="h-5 w-5 animate-spin text-[#5B8DEF]" />
                </div>
              ) : error ? (
                <ErrorState
                  message={error}
                  onRetry={() => setFetchTick((t) => t + 1)}
                />
              ) : filtered.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-3">
                  {filtered.map((alert) => (
                    <AlertCard
                      key={alert.id}
                      alert={alert}
                      onAcknowledge={handleAcknowledge}
                    />
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
