"use client";

import {
  AlertCard,
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
  fetchIncidents,
  normaliseAlert,
  getAuthToken,
  WS_BASE,
  broadcastAlert,
  updateAlertStatus,
  type AlertFilters,
  type AlertClosingStatus,
  type IncidentSummary,
} from "@/lib/api/alert";

import { toast } from "sonner";
import { claimTrackingEvent } from "@/lib/tracking-events";
import {
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  type MutableRefObject,
} from "react";

const ALL_SEVERITIES: AlertSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const ALL_STATUSES: AlertStatus[] = ["NEW", "ACKNOWLEDGED", "CONFIRMED", "RESOLVED", "DISMISSED"];
const CURRENT_CUTOFF = 24 * 60 * 60 * 1000; // 24h

const SEVERITY_LABELS: Record<AlertSeverity, string> = {
  CRITICAL: "Critical",
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
};

const STATUS_LABELS: Record<AlertStatus, string> = {
  NEW: "New",
  ACKNOWLEDGED: "Responding",
  CONFIRMED: "Confirmed",
  RESOLVED: "Resolved",
  DISMISSED: "Dismissed"
};

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center" role="status" aria-live="polite">
      <p className="text-base font-semibold text-brand-ash">No alerts</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <p className="text-base font-semibold text-brand-threat">Failed to load alerts</p>
      <p className="max-w-xs text-xs text-brand-ash">{message}</p>
      <Button size="sm" variant="outline" onClick={onRetry} className="border-border bg-transparent text-brand-ash hover:bg-brand-slate hover:text-brand-frost text-xs">
        Try again
      </Button>
    </div>
  );
}

function ActionErrorBanner({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <div role="alert" className="mb-4 flex items-center gap-2 rounded-lg border border-brand-threat/30 bg-brand-threat/10 px-4 py-3 text-sm text-brand-threat">
      <span className="flex-1">{message}</span>
      <button type="button" onClick={onDismiss} aria-label="Dismiss error" className="ml-2 text-brand-threat/60 transition-colors hover:text-brand-threat">✕</button>
    </div>
  );
}

type FetchState = {
  incidents: IncidentSummary[];
  loading: boolean;
  error: string | null;
};

type FetchAction =
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; payload: IncidentSummary[] }
  | { type: "FETCH_ERROR"; payload: string }
  | { type: "UPDATE_INCIDENT"; payload: IncidentSummary };

const initialFetchState: FetchState = {
  incidents: [],
  loading: true,
  error: null,
};

function fetchReducer(
  state: FetchState,
  action: FetchAction,
): FetchState {
  switch (action.type) {
    case "FETCH_START":
      return {
        ...state,
        loading: true,
        error: null,
      };

    case "FETCH_SUCCESS":
      return {
        incidents: action.payload,
        loading: false,
        error: null,
      };

    case "FETCH_ERROR":
      return {
        ...state,
        loading: false,
        error: action.payload,
      };

    case "UPDATE_INCIDENT":
      return {
        ...state,
        incidents: state.incidents.map((incident) =>
          incident.id === action.payload.id
            ? action.payload
            : incident,
        ),
      };

    default:
      return state;
  }
}
interface Props {
  neighbourhoodId: string;
}


type AlertSocketMessage = {
  event: string;
  payload?: Record<string, unknown>;
};

function handleTrackingSightingMessage(
  payload: Record<string, unknown>,
  seenEventIds: Set<string>,
  onRefresh: () => void,
): void {
  if (!claimTrackingEvent(payload.event_id, seenEventIds)) {
    return;
  }

  const cameraName =
    typeof payload.camera_name === "string"
      ? payload.camera_name
      : "another camera";

  const cameraLocation =
    typeof payload.camera_location === "string"
      ? payload.camera_location
      : "location unavailable";

  const sequenceNumber =
    typeof payload.sequence_no === "number"
      ? payload.sequence_no
      : "?";

  toast.info("Cross-property match detected", {
    id: `tracking-match-${String(payload.event_id)}`,
    description: `${cameraName} · ${cameraLocation} · sequence ${sequenceNumber}`,
  });

  onRefresh();
}

function handleAlertSocketMessage(
  message: AlertSocketMessage,
  isSecurityOfficer: boolean,
  seenEventIds: Set<string>,
  onIncidentRefresh: () => void,
  onTrackingRefresh: () => void,
): void {
  if (message.event === "ping") {
    return;
  }

  if (message.event === "tracking.sighting") {
    if (message.payload) {
      handleTrackingSightingMessage(
        message.payload,
        seenEventIds,
        onTrackingRefresh,
      );
    }

    return;
  }


  if (message.event === "incident.updated") {
    onIncidentRefresh();
    return;
  }

  if (!message.payload) {
    return;
  }

  const incomingAlert = normaliseAlert(message.payload);

  if (message.event === "alert.new") {
    if (
      isSecurityOfficer &&
      getSeverity(incomingAlert.detection_type) !== "CRITICAL"
    ) {
      return;
    }

    onIncidentRefresh();

    return;
  }

  if (message.event === "alert.acknowledged" || message.event === "alert.resolved" || message.event === "alert.dismissed") {
    onIncidentRefresh();
  }
}


type AlertsWebSocketOptions = {
  url: string;
  wsRef: MutableRefObject<WebSocket | null>;
  mountedRef: MutableRefObject<boolean>;
  isSecurityOfficer: boolean;
  seenEventIds: Set<string>;
  onIncidentRefresh: () => void;
  onTrackingRefresh: () => void;
  onConnectionChange: (connected: boolean) => void;
};

function createAlertsWebSocket({
  url,
  wsRef,
  mountedRef,
  isSecurityOfficer,
  seenEventIds,
  onIncidentRefresh,
  onTrackingRefresh,
  onConnectionChange,
}: AlertsWebSocketOptions): () => void {
  let unmounted = false;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  const connect = (): void => {
    if (unmounted) {
      return;
    }

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (mountedRef.current) {
        onConnectionChange(true);
      }
    };

    ws.onclose = () => {
      if (mountedRef.current) {
        onConnectionChange(false);
      }

      if (!unmounted) {
        reconnectTimer = setTimeout(connect, 3_000);
      }
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) {
        return;
      }

      try {
        const message = JSON.parse(event.data as string) as AlertSocketMessage;

        handleAlertSocketMessage(
          message,
          isSecurityOfficer,
          seenEventIds,
          onIncidentRefresh,
          onTrackingRefresh,
        );
      } catch {
        // Ignore malformed WebSocket payloads.
      }
    };
  };

  connect();

  return () => {
    unmounted = true;

    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer);
    }

    const ws = wsRef.current;

    if (ws) {
      ws.onclose = null;
      ws.close();
    }
  };
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

  const isSystemAdmin =
  userContext?.user.system_role === "SYSTEM_ADMIN";

  const isNeighbourhoodAdmin =
    neighbourhoodRole === "NEIGHBOURHOOD_ADMIN";

  const isSecurityOfficer =
    neighbourhoodRole === "SECURITY_OFFICER";

  const canViewAlerts =
    isSystemAdmin || isNeighbourhoodAdmin || isSecurityOfficer;

  const canViewTracking =
    isSystemAdmin || isNeighbourhoodAdmin || isSecurityOfficer;

  const [{ incidents, loading, error }, dispatch] = useReducer(fetchReducer, initialFetchState);

  const [actionError, setActionError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [fetchTick, setFetchTick] = useState(0);

  const [trackingRefreshKey, setTrackingRefreshKey] = useState(0);

  const [selectedSeverities, setSelectedSeverities] = useState<Set<AlertSeverity>>(new Set(ALL_SEVERITIES));
  const [selectedStatus, setSelectedStatus] = useState<AlertStatus | null>(null);
  const [activeTab, setActiveTab] = useState<"current" | "history">("current");
  const [historyStartDate, setHisoryStartDate] = useState("");
  const [historyEndDate, setHisoryEndDate] = useState("");
  const [broadcastingAlertId, setBroadcastingAlertId] = useState<string | null>(null);

  const seenTrackingEventIdsRef = useRef<Set<string>>(new Set());

  const alertFilters = useMemo<AlertFilters>(() => {
    const base: AlertFilters = {};
    if (selectedStatus) base.status = selectedStatus;
    if (activeTab === "history") {
      if (historyStartDate) base.startDate = new Date(historyStartDate);
      if (historyEndDate) {
        base.endDate = new Date(
          `${historyEndDate}T23:59:59.999`,
        );
      }
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

    fetchIncidents(neighbourhoodId, filters, controller.signal)
      .then(({ incidents: fetched }) => {
        if (!mountedRef.current) return;

        dispatch({
          type: "FETCH_SUCCESS",
          payload: fetched,
        });
      })
      .catch((err: unknown) => {
        if (!mountedRef.current) return;
        if (err instanceof DOMException && err.name === "AbortError") return;
        dispatch({ type: "FETCH_ERROR", payload: err instanceof Error ? err.message : "Unknown error" });
      });

    return () => controller.abort();
  }, [neighbourhoodId, fetchTick, alertFilters, activeTab, userContextLoading, canViewAlerts]);

  useEffect(() => {
    if (activeTab !== "current" || userContextLoading || !canViewAlerts) {
      return;
    }

    const token = getAuthToken();
    const url = `${WS_BASE}/alerts/${neighbourhoodId}/ws${token ? `?token=${token}` : ""}`;

    return createAlertsWebSocket({
      url,
      wsRef,
      mountedRef,
      isSecurityOfficer,
      seenEventIds: seenTrackingEventIdsRef.current,
      onIncidentRefresh: () => {
        dispatch({ type: "FETCH_START" });
        setFetchTick((tick) => tick + 1);
      },
      onTrackingRefresh: () => {
        setTrackingRefreshKey((current) => current + 1);
      },
      onConnectionChange: setWsConnected,
    });
  }, [neighbourhoodId, activeTab, userContextLoading, canViewAlerts, isSecurityOfficer]);

  async function handleCloseAlert(
    id: string,
    status: AlertClosingStatus,
  ): Promise<void> {
    const incident = incidents.find(
      (item) => item.representative_alert.id === id,
    );

    if (!incident) return;

    setActionError(null);

    try {
      await updateAlertStatus(id, status);
      if (mountedRef.current) triggerRefresh();
    } catch (error) {
      if (!mountedRef.current) return;

      setActionError(
        error instanceof Error
          ? error.message
          : "Failed to update alert",
      );
      console.error("Failed to close alert:", error);
    }
  }


  async function handleBroadcast(id: string) {
    const incident = incidents.find(
      (item) => item.representative_alert.id === id,
    );

    const alert = incident?.representative_alert;

    if (!alert || alert.status === "RESOLVED") {
      return;
    }

    setActionError(null);
    setBroadcastingAlertId(id);

    try {
      await broadcastAlert(id);
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Failed to broadcast the alert.",
      );

      console.error("Broadcast alert failed:", err);
    } finally {
      if (mountedRef.current) {
        setBroadcastingAlertId(null);
      }
    }
  }

  const filteredIncidents = useMemo(
    () =>
      incidents.filter((incident) =>
        selectedSeverities.has(
          getSeverity(
            incident.representative_alert.detection_type,
          ),
        ),
      ),
    [incidents, selectedSeverities],
  );

  const hasActiveFilters =
    selectedSeverities.size < ALL_SEVERITIES.length ||
    selectedStatus !== null ||
    (activeTab === "history" &&
      (historyStartDate !== "" || historyEndDate !== ""));

  const newCount = filteredIncidents.filter(
    (incident) =>
      incident.representative_alert.status === "NEW",
  ).length;

  const criticalCount = filteredIncidents.filter(
    (incident) =>
      getSeverity(
        incident.representative_alert.detection_type,
      ) === "CRITICAL" &&
      incident.representative_alert.status === "NEW",
  ).length;

  if (userContextLoading) {
    return (
      <main className="min-h-full bg-brand-void px-0 py-4 text-brand-frost sm:px-2 sm:py-6 md:px-4 md:py-8">
        <div className="mx-auto flex max-w-6xl items-center justify-center py-20">
          <RefreshCw className="size-5 animate-spin text-brand-green" />
        </div>
      </main>
    );
  }

  if (!canViewAlerts) {
    return (
      <main className="min-h-full bg-brand-void px-0 py-4 text-brand-frost sm:px-2 sm:py-6 md:px-4 md:py-8">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm text-brand-ash">
            You do not have access to these alerts.
          </p>
        </div>
      </main>
    );
  }


  return (
    <TooltipProvider>
      <main className="min-h-full bg-brand-void px-0 py-4 text-brand-frost sm:px-2 sm:py-6 md:px-4 md:py-8">
        <div className="mx-auto w-full max-w-6xl">
          <header className="mb-7 border-b border-border pb-6">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight text-brand-frost">{isNeighbourhoodAdmin ? "Live alerts" : "Critical alerts"}</h1>
              <span title={wsConnected ? "Live updates connected" : "Live updates disconnected"} aria-label={wsConnected ? "Live" : "Offline"}>
                {wsConnected ? <Wifi className="h-4 w-4 text-brand-green mt-1" /> : <WifiOff className="h-4 w-4 text-brand-ash/60 mt-1" />}
              </span>
            </div>

            <p className="mt-2 max-w-xl text-sm leading-relaxed text-brand-ash">
              {isNeighbourhoodAdmin
                ? "Monitor alerts across your neighbourhood and broadcast incidents when needed."
                : "Review critical events that require a security response."}
            </p>


            {(newCount > 0 || criticalCount > 0) && (
              <div className="mt-3 flex flex-wrap justify-center gap-2" aria-live="polite">
                {newCount > 0 && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-brand-green/25 bg-brand-green/10 px-3 py-1 text-xs font-semibold text-brand-green">
                    {newCount} new
                  </span>
                )}
                {criticalCount > 0 && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-brand-threat/25 bg-brand-threat/10 px-3 py-1 text-xs font-semibold text-brand-threat">
                    {criticalCount} critical
                  </span>
                )}
              </div>
            )}
          </header>

          {actionError && <ActionErrorBanner message={actionError} onDismiss={() => setActionError(null)} />}

          <div className="mb-5 flex gap-2" role="tablist">
            <Button role="tab" aria-selected={activeTab === "current"} size="sm" variant={activeTab === "current" ? "default" : "outline"} onClick={() => setActiveTab("current")} className={activeTab === "current" ? "bg-brand-green text-brand-void hover:bg-brand-green text-xs font-medium" : "border-border bg-transparent text-brand-ash hover:bg-brand-slate hover:text-brand-frost text-xs font-medium"}>
              Current
            </Button>
            <Button role="tab" aria-selected={activeTab === "history"} size="sm" variant={activeTab === "history" ? "default" : "outline"} onClick={() => setActiveTab("history")} className={activeTab === "history" ? "bg-brand-green text-brand-void hover:bg-brand-green text-xs font-medium" : "border-border bg-transparent text-brand-ash hover:bg-brand-slate hover:text-brand-frost text-xs font-medium"}>
              History
            </Button>
          </div>

          <Card className="overflow-hidden rounded-lg border border-border bg-brand-depth">
            <div className="flex items-center justify-between gap-3 rounded-t-xl border-b border-border px-3 py-3 sm:px-5 sm:py-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className={`text-xs font-medium transition-colors bg-transparent ${hasActiveFilters ? "border-brand-green text-brand-green" : "border-border text-brand-ash"}`}
                    aria-label="Open filter options"
                  >
                    <SlidersHorizontal className="mr-1.5 h-3.5 w-3.5" />
                    Filter
                    {hasActiveFilters && (
                      <span className="ml-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-brand-green text-xs font-bold text-brand-void">
                        !
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent align="start" className="w-52 border-border bg-brand-abyss text-brand-frost">
                  <DropdownMenuLabel className="text-xs uppercase tracking-wider text-brand-ash">Severity</DropdownMenuLabel>
                  {ALL_SEVERITIES.map((severity) => (
                    <DropdownMenuCheckboxItem
                      key={severity}
                      className="cursor-pointer text-sm text-brand-frost focus:bg-brand-slate focus:text-brand-frost"
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

                  <DropdownMenuSeparator className="bg-brand-slate" />
                  <DropdownMenuLabel className="text-xs uppercase tracking-wider text-brand-ash">Status</DropdownMenuLabel>
                  <DropdownMenuCheckboxItem className="cursor-pointer text-sm text-brand-frost focus:bg-brand-slate focus:text-brand-frost" checked={selectedStatus === null} onCheckedChange={() => setSelectedStatus(null)}>
                    All
                  </DropdownMenuCheckboxItem>
                  {ALL_STATUSES.map((status) => (
                    <DropdownMenuCheckboxItem key={status} className="cursor-pointer text-sm text-brand-frost focus:bg-brand-slate focus:text-brand-frost" checked={selectedStatus === status} onCheckedChange={(checked) => setSelectedStatus(checked ? status : null)}>
                      {STATUS_LABELS[status]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  {activeTab === "history" && (
                    <>
                      <DropdownMenuSeparator className="bg-brand-slate" />
                      <DropdownMenuLabel className="text-xs uppercase tracking-wider text-brand-ash">Date range</DropdownMenuLabel>
                      <div className="flex flex-col gap-2 px-2 py-1.5">
                        <label className="text-xs text-brand-ash">
                          From
                          <input type="date" value={historyStartDate} onChange={(event) => setHisoryStartDate(event.target.value)} className="mt-1 w-full rounded border border-border bg-brand-abyss px-2 py-1 text-xs text-brand-frost" />
                        </label>
                        <label className="text-xs text-brand-ash">
                          To
                          <input type="date" value={historyEndDate} onChange={(event) => setHisoryEndDate(event.target.value)} className="mt-1 w-full rounded border border-border bg-brand-abyss px-2 py-1 text-xs text-brand-frost" />
                        </label>
                      </div>
                    </>
                  )}

                  {hasActiveFilters && (
                    <>
                      <DropdownMenuSeparator className="bg-brand-slate" />
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedSeverities(new Set(ALL_SEVERITIES));
                          setSelectedStatus(null);
                          setHisoryStartDate("");
                          setHisoryEndDate("");
                        }}
                        className="w-full px-2 py-1.5 text-left text-xs text-brand-green transition-colors hover:text-brand-green"
                      >
                        Clear all filters
                      </button>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              <Button variant="ghost" size="sm" onClick={triggerRefresh} disabled={loading} className="text-brand-green hover:text-brand-frost hover:bg-brand-slate transition-colors text-xs" aria-label="Refresh alerts">
                <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>

            <section
              aria-label="Alert list"
              aria-live="polite"
              className="rounded-b-lg p-3 sm:p-5 md:p-6"
            >

              {loading && incidents.length === 0 ? (
                <div className="flex items-center justify-center py-20">
                  <RefreshCw className="h-5 w-5 animate-spin text-brand-green" />
                </div>
              ) : error ? (
                <ErrorState message={error} onRetry={() => setFetchTick((tick) => tick + 1)} />
              ) : filteredIncidents.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-3">
                  {filteredIncidents.map((incident) => {
                    const representativeAlert =
                      incident.representative_alert;
                    const isInProgress =
                      representativeAlert.status === "ACKNOWLEDGED" ||
                      representativeAlert.status === "CONFIRMED";

                    const canResolve =
                      isNeighbourhoodAdmin ||
                      (isSecurityOfficer && isInProgress);
                    const canDismiss =
                      isNeighbourhoodAdmin ||
                      (isSecurityOfficer && isInProgress);

                    return (
                      <AlertCard
                        key={incident.id}
                        alert={representativeAlert}
                        alertCount={incident.alert_count}
                        onResolve={
                          canResolve
                            ? (id) => handleCloseAlert(id, "RESOLVED")
                            : undefined
                        }
                        onDismissAlert={
                          canDismiss
                            ? (id) => handleCloseAlert(id, "DISMISSED")
                            : undefined
                        }
                        onBroadcast={
                          isNeighbourhoodAdmin
                            ? handleBroadcast
                            : undefined
                        }
                        broadcasting={
                          broadcastingAlertId === representativeAlert.id
                        }
                        canViewTracking={canViewTracking}
                        trackingRefreshKey={trackingRefreshKey}
                      />
                    );
                  })}

                </div>
              )}
            </section>
          </Card>
        </div>
      </main>
    </TooltipProvider>
  );
}
