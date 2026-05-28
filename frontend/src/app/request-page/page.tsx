"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from "react";
import {
  RequestCard,
  type JoinRequest,
  type JoinRequestStatus,
} from "@/components/shared/RequestCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Loader2, RefreshCw, AlertCircle } from "lucide-react";
import {
  fetchJoinRequests,
  resolveJoinRequest,
  ApiError,
} from "@/lib/api/neighbourhoodJoin";

const ALL_STATUSES: JoinRequestStatus[] = ["PENDING", "APPROVED", "DENIED"];

const STATUS_LABELS: Record<JoinRequestStatus | "ALL", string> = {
  ALL: "All",
  PENDING: "Pending",
  APPROVED: "Approved",
  DENIED: "Denied",
};

type FilterValue = JoinRequestStatus | "ALL";

function EmptyState({ filter }: { filter: FilterValue }) {
  return (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      role="status"
      aria-live="polite"
    >
      <p className="text-base font-semibold text-mist/50">
        No {filter === "ALL" ? "" : STATUS_LABELS[filter].toLowerCase()}{" "}
        requests
      </p>
    </div>
  );
}

function ErrorBanner({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex items-center gap-2 rounded-lg border border-threat/30 bg-threat/10 px-4 py-3 text-sm text-threat mb-4"
    >
      <AlertCircle className="h-4 w-4 shrink-0" />
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

function ActionErrorBanner({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return <ErrorBanner message={message} onDismiss={onDismiss} />;
}

type FetchState = {
  requests: JoinRequest[];
  loading: boolean;
  error: string | null;
};

type FetchAction =
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; payload: JoinRequest[] }
  | { type: "FETCH_ERROR"; payload: string }
  | { type: "DISMISS_ERROR" }
  | { type: "UPDATE_REQUEST"; payload: JoinRequest };

const initialFetchState: FetchState = {
  requests: [],
  loading: true,
  error: null,
};

function fetchReducer(state: FetchState, action: FetchAction): FetchState {
  switch (action.type) {
    case "FETCH_START":
      return { ...state, loading: true, error: null };
    case "FETCH_SUCCESS":
      return { requests: action.payload, loading: false, error: null };
    case "FETCH_ERROR":
      return { ...state, loading: false, error: action.payload };
    case "DISMISS_ERROR":
      return { ...state, error: null };
    case "UPDATE_REQUEST":
      return {
        ...state,
        requests: state.requests.map((r) =>
          r.id === action.payload.id ? { ...r, ...action.payload } : r,
        ),
      };
  }
}

export default function JoinRequestsPage() {
  const [{ requests, loading, error }, dispatch] = useReducer(
    fetchReducer,
    initialFetchState,
  );
  const [activeFilter, setActiveFilter] = useState<FilterValue>("PENDING");
  const [actionError, setActionError] = useState<string | null>(null);

  // Incrementing this triggers a re-fetch without needing a stable callback ref.
  const [fetchTick, setFetchTick] = useState(0);

  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    dispatch({ type: "FETCH_START" });

    fetchJoinRequests(controller.signal)
      .then((data) => {
        if (!mountedRef.current) return;
        dispatch({ type: "FETCH_SUCCESS", payload: data });
      })
      .catch((err: unknown) => {
        if (!mountedRef.current) return;
        if (err instanceof DOMException && err.name === "AbortError") return;
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : "Failed to load join requests.";
        dispatch({ type: "FETCH_ERROR", payload: message });
      });

    return () => controller.abort();
  }, [fetchTick]);

  const handleApprove = useCallback(async (id: string) => {
    setActionError(null);
    try {
      const updated = await resolveJoinRequest(id, "APPROVE");
      dispatch({ type: "UPDATE_REQUEST", payload: updated });
    } catch (err) {
      setActionError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Failed to approve join request.",
      );
    }
  }, []);

  const handleDeny = useCallback(async (id: string) => {
    setActionError(null);
    try {
      const updated = await resolveJoinRequest(id, "DENY");
      dispatch({ type: "UPDATE_REQUEST", payload: updated });
    } catch (err) {
      setActionError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Failed to deny join request.",
      );
    }
  }, []);

  const filtered = useMemo(
    () =>
      activeFilter === "ALL"
        ? requests
        : requests.filter((r) => r.status === activeFilter),
    [requests, activeFilter],
  );

  const pendingCount = requests.filter((r) => r.status === "PENDING").length;

  return (
    <div className="w-full flex flex-col items-center px-8 py-10 bg-navy min-h-full font-sans">
      <div className="w-full max-w-2xl">
        <header className="mb-6 text-center">
          <h1 className="text-[2rem] font-bold leading-10 text-white">
            Join Requests
          </h1>

          {pendingCount > 0 && (
            <div
              className="flex gap-2 mt-3 flex-wrap justify-center"
              aria-live="polite"
            >
              <span className="inline-flex items-center gap-1 text-xs font-semibold bg-blue/20 border border-blue/30 rounded-full px-3 py-1 text-sky">
                {pendingCount} pending
              </span>
            </div>
          )}
        </header>

        {error && (
          <ErrorBanner
            message={error}
            onDismiss={() => dispatch({ type: "DISMISS_ERROR" })}
          />
        )}

        {actionError && (
          <ActionErrorBanner
            message={actionError}
            onDismiss={() => setActionError(null)}
          />
        )}

        <Card className="bg-steel/40 border-steel rounded-xl">
          {/* Toolbar */}
          <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-steel rounded-t-xl">
            {/* Filter tabs */}
            <div className="flex items-center bg-navy/70 border border-steel rounded-lg overflow-hidden">
              {(
                ["PENDING", ...ALL_STATUSES.slice(1), "ALL"] as FilterValue[]
              ).map((f, i, arr) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setActiveFilter(f)}
                  className={[
                    "text-xs font-medium px-3 py-1.5 transition-colors duration-100",
                    i < arr.length - 1 ? "border-r border-steel" : "",
                    activeFilter === f
                      ? "bg-blue/25 text-sky"
                      : "text-mist hover:bg-steel hover:text-white",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  {STATUS_LABELS[f]}
                </button>
              ))}
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setFetchTick((t) => t + 1)}
              disabled={loading}
              className="text-sky hover:text-white hover:bg-steel transition-colors text-xs"
              aria-label="Refresh requests"
            >
              {loading ? (
                <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
              )}
              Refresh
            </Button>
          </div>

          {/* List */}
          <section
            aria-label="Join request list"
            aria-live="polite"
            className="p-4 rounded-b-xl"
          >
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-6 w-6 animate-spin text-sky" />
              </div>
            ) : filtered.length === 0 ? (
              <EmptyState filter={activeFilter} />
            ) : (
              <div className="space-y-2.5">
                {filtered.map((req) => (
                  <RequestCard
                    key={req.id}
                    request={req}
                    onApprove={handleApprove}
                    onDeny={handleDeny}
                  />
                ))}
              </div>
            )}
          </section>
        </Card>
      </div>
    </div>
  );
}
