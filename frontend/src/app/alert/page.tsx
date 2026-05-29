"use client";

import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
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
  fetchCurrentUser,
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
      {/*
        On a light background, use --color-body (muted navy-grey) for de-emphasised text.
        --color-mist would be near-invisible on white; --color-body gives enough contrast.
      */}
      <p
        className="text-base font-semibold"
        style={{ color: "var(--color-body)" }}
      >
        No alerts
      </p>
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
      <p className="text-base font-semibold text-threat">
        Failed to load alerts
      </p>
      <p className="text-xs text-mist max-w-xs">{message}</p>
      <Button
        size="sm"
        variant="outline"
        onClick={onRetry}
        className="border-steel text-mist hover:bg-steel hover:text-white text-xs"
      >
        Try again
      </Button>
    </div>
  );
}

function ActionErrorBanner({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div
      role="alert"
      className="mb-4 flex items-center gap-2 rounded-lg border border-threat/30 bg-threat/10 px-4 py-3 text-sm text-threat"
    >
      <span className="flex-1">{message}</span>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss error"
        className="ml-2 text-threat/60 hover:text-threat transition-colors"
      >
        ✕
      </button>
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
  neighbourhoodId?: string;
}

export default function AlertsPage({
  neighbourhoodId: initialNeighbourhoodId,
}: Props) {
  const [{ alerts, loading, error }, dispatch] = useReducer(
    fetchReducer,
    initialFetchState,
  );
  const searchParams = useSearchParams();
  const queryNeighbourhoodId =
    searchParams.get("neighbourhoodId") || searchParams.get("neighbourhood_id");
  const [neighbourhoodId, setNeighbourhoodId] = useState<string | null>(
    initialNeighbourhoodId ?? queryNeighbourhoodId ?? null,
  );
  const [identityLoading, setIdentityLoading] = useState(
    !initialNeighbourhoodId && !queryNeighbourhoodId,
  );
  const [identityError, setIdentityError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
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
    if (initialNeighbourhoodId || queryNeighbourhoodId) {
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
        if (!cancelled) setIdentityLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [initialNeighbourhoodId, queryNeighbourhoodId]);

  useEffect(() => {
    if (!neighbourhoodId) return;

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
    if (!neighbourhoodId) return;

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
    if (!original || original.status !== "NEW") return;

    setActionError(null);
    dispatch({
      type: "UPDATE_ALERT",
      payload: { ...original, status: "ACKNOWLEDGED" },
    });

    try {
      await acknowledgeAlert(id);
    } catch (err) {
      if (mountedRef.current) {
        dispatch({ type: "UPDATE_ALERT", payload: original });
        setActionError(
          err instanceof Error ? err.message : "Failed to acknowledge alert.",
        );
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

  if (identityLoading) {
    return (
      <TooltipProvider>
        <div className="w-full min-h-full flex items-center justify-center px-8 py-10 bg-navy text-mist">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin text-sky" />
            Resolving neighbourhood context...
          </div>
        </div>
      </TooltipProvider>
    );
  }

  if (!neighbourhoodId) {
    return (
      <TooltipProvider>
        <div className="w-full min-h-full flex items-center justify-center px-8 py-10 bg-navy text-center">
          <Card className="max-w-md bg-steel/40 border-steel rounded-xl p-6 text-white">
            <p className="text-lg font-semibold">Alerts need a neighbourhood</p>
            <p className="mt-2 text-sm text-mist">
              {identityError ||
                "Open this page with a neighbourhood ID, or sign in to a user that already belongs to one."}
            </p>
          </Card>
        </div>
      </TooltipProvider>
    );
  }

  return (
    <TooltipProvider>
      <div className="w-full flex flex-col items-center px-8 py-10 bg-navy min-h-full font-sans">
        <div className="w-full max-w-2xl">
          <header className="mb-6 text-center">
            <div className="flex items-center justify-center gap-2">
              <h1 className="text-[2rem] font-bold leading-[2.5rem] text-white">
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
                  <Wifi className="h-4 w-4 text-safe mt-1" />
                ) : (
                  <WifiOff className="h-4 w-4 text-mist/50 mt-1" />
                )}
              </span>
            </div>

            {(newCount > 0 || criticalCount > 0) && (
              <div
                className="flex gap-2 mt-3 flex-wrap justify-center"
                aria-live="polite"
              >
                {newCount > 0 && (
                  /*
                    "New" informational badge: --color-blue tint bg, --color-blue text.
                    --color-blue on white-ish fog meets ≥ 4.5:1 for small text.
                  */
                  <span
                    className="inline-flex items-center gap-1 text-xs font-semibold rounded-full px-3 py-1"
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
                  /*
                    Critical badge: --color-threat tint bg, --color-threat text.
                    Solid threat red on light bg comfortably exceeds 4.5:1.
                  */
                  <span
                    className="inline-flex items-center gap-1 text-xs font-semibold rounded-full px-3 py-1"
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

          {actionError && (
            <ActionErrorBanner
              message={actionError}
              onDismiss={() => setActionError(null)}
            />
          )}

          <Card className="bg-steel/40 border-steel rounded-xl">
            {/* Toolbar */}
            <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-steel rounded-t-xl">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs font-medium transition-colors"
                    style={{
                      /*
                        Default: --color-mist border, --color-body text (readable on white).
                        Active: --color-blue border + text to signal filter is on.
                      */
                      borderColor: hasActiveFilters
                        ? "var(--color-blue)"
                        : "var(--color-mist)",
                      backgroundColor: "transparent",
                      color: hasActiveFilters
                        ? "var(--color-blue)"
                        : "var(--color-body)",
                    }}
                    aria-label="Open filter options"
                  >
                    <SlidersHorizontal className="h-3.5 w-3.5 mr-1.5" />
                    Filter
                    {hasActiveFilters && (
                      /*
                        Active-filter pip: --color-blue fill, white label.
                        White on --color-blue ≥ 4.5:1 per spec contrast table.
                      */
                      <span
                        className="ml-1.5 flex h-4 w-4 items-center justify-center rounded-full text-xs font-bold"
                        style={{
                          backgroundColor: "var(--color-blue)",
                          color: "var(--color-white)",
                        }}
                      >
                        !
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>

                {/*
                  Dropdown: white bg, mist border, ink text.
                  The dropdown sits above the light page so it stays white (not navy).
                */}
                <DropdownMenuContent
                  align="start"
                  className="w-52"
                  style={{
                    backgroundColor: "var(--color-white)",
                    borderColor: "var(--color-mist)",
                    color: "var(--color-ink)",
                  }}
                >
                  {/* Section label: caption-weight, --color-body for subdued tone */}
                  <DropdownMenuLabel
                    className="text-xs uppercase tracking-wider"
                    style={{ color: "var(--color-body)" }}
                  >
                    Severity
                  </DropdownMenuLabel>
                  {ALL_SEVERITIES.map((sev) => (
                    <DropdownMenuCheckboxItem
                      key={sev}
                      className="text-sm cursor-pointer"
                      style={{ color: "var(--color-ink)" }}
                      checked={selectedSeverities.has(sev)}
                      onCheckedChange={(checked) => {
                        setSelectedSeverities((prev) => {
                          const next = new Set(prev);
                          if (checked) {
                            next.add(sev);
                          } else {
                            next.delete(sev);
                          }
                          return next;
                        });
                      }}
                    >
                      {SEVERITY_LABELS[sev]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  <DropdownMenuSeparator
                    style={{ backgroundColor: "var(--color-mist)" }}
                  />

                  <DropdownMenuLabel
                    className="text-xs uppercase tracking-wider"
                    style={{ color: "var(--color-body)" }}
                  >
                    Status
                  </DropdownMenuLabel>
                  {ALL_STATUSES.map((st) => (
                    <DropdownMenuCheckboxItem
                      key={st}
                      className="text-sm cursor-pointer"
                      style={{ color: "var(--color-ink)" }}
                      checked={selectedStatuses.has(st)}
                      onCheckedChange={(checked) => {
                        setSelectedStatuses((prev) => {
                          const next = new Set(prev);
                          if (checked) {
                            next.add(st);
                          } else {
                            next.delete(st);
                          }
                          return next;
                        });
                      }}
                    >
                      {STATUS_LABELS[st]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  {hasActiveFilters && (
                    <>
                      <DropdownMenuSeparator
                        style={{ backgroundColor: "var(--color-mist)" }}
                      />
                      {/* Ghost: --color-blue text, no border — readable on white */}
                      <button
                        onClick={() => {
                          setSelectedSeverities(new Set(ALL_SEVERITIES));
                          setSelectedStatuses(new Set(["NEW", "ACKNOWLEDGED"]));
                        }}
                        className="w-full text-left px-2 py-1.5 text-xs transition-colors"
                        style={{ color: "var(--color-blue)" }}
                        onMouseEnter={(e) =>
                          (e.currentTarget.style.color = "var(--color-navy)")
                        }
                        onMouseLeave={(e) =>
                          (e.currentTarget.style.color = "var(--color-blue)")
                        }
                      >
                        Clear all filters
                      </button>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              {/*
                Ghost refresh button: --color-blue text on white card.
                Hover darkens to --color-navy, staying within the brand palette.
              */}
              <Button
                variant="ghost"
                size="sm"
                onClick={triggerRefresh}
                disabled={loading}
                className="text-sky hover:text-white hover:bg-steel transition-colors text-xs"
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
              className="p-4 rounded-b-xl"
            >
              {loading && alerts.length === 0 ? (
                <div className="flex items-center justify-center py-20">
                  <RefreshCw className="h-5 w-5 animate-spin text-sky" />
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