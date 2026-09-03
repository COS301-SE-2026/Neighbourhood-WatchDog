"use client";

import {
    useCallback,
    useEffect,
    useMemo,
    useReducer,
    useRef,
    useState,
} from "react";

import { useParams } from "next/navigation";
import {
    AlertCircle,
    Loader2,
    RefreshCw,
} from "lucide-react";

import {
    RequestCard,
    type JoinRequest,
    type JoinRequestStatus,
} from "@/components/shared/RequestCard";

import {
    fetchJoinRequests,
    resolveJoinRequest,
    fetchJoinCodeRequest,
    regenerateJoinCodeRequest,
    ApiError,
} from "@/lib/api/neighbourhoodJoin";
import { useUserContext } from "@/hooks/use-user-context";

const ALL_STATUSES: JoinRequestStatus[] = [
    "PENDING",
    "APPROVED",
    "DENIED",
];

const STATUS_LABELS: Record<JoinRequestStatus | "ALL", string> = {
    ALL: "All",
    PENDING: "Pending",
    APPROVED: "Approved",
    DENIED: "Denied",
};

type FilterValue = JoinRequestStatus | "ALL";

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
                requests: action.payload,
                loading: false,
                error: null,
            };

        case "FETCH_ERROR":
            return {
                ...state,
                loading: false,
                error: action.payload,
            };

        case "DISMISS_ERROR":
            return {
                ...state,
                error: null,
            };

        case "UPDATE_REQUEST":
            return {
                ...state,
                requests: state.requests.map((request) =>
                    request.id === action.payload.id
                        ? { ...request, ...action.payload }
                        : request,
                ),
            };
    }
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
            className="mb-5 flex items-start gap-3 border border-brand-threat/25 bg-brand-threat/10 px-4 py-3 text-sm text-brand-threat"
        >
            <AlertCircle className="mt-0.5 size-4 shrink-0 text-brand-threat" />

            <p className="flex-1 leading-relaxed">{message}</p>

            <button
                type="button"
                onClick={onDismiss}
                aria-label="Dismiss error"
                className="text-brand-threat/60 transition-colors hover:text-brand-threat"
            >
                ×
            </button>
        </div>
    );
}

function EmptyState({ filter }: { filter: FilterValue }) {
    const filterLabel =
        filter === "ALL"
            ? "No join requests yet"
            : `No ${STATUS_LABELS[filter].toLowerCase()} requests`;

    return (
        <div
            className="border-t border-border py-16 text-center"
            role="status"
            aria-live="polite"
        >
            <p className="text-sm font-medium text-brand-ash">
                {filterLabel}
            </p>

            <p className="mt-2 text-sm text-brand-ash/70">
                New requests will appear here when residents ask to join this
                neighbourhood.
            </p>
        </div>
    );
}

export default function JoinRequestsPage() {

    const { neighbourhoodId } = useParams<{neighbourhoodId: string }>();
    const { data: userContext, isLoading: userContextLoading } = useUserContext();

    const adminProperty = userContext?.properties.find(
        (p) => p.neighbourhood?.id === neighbourhoodId && p.is_admin
    );

    const [{ requests, loading, error }, dispatch] = useReducer(
        fetchReducer,
        initialFetchState,
    );

    const [activeFilter, setActiveFilter] =
        useState<FilterValue>("PENDING");

    const [actionError, setActionError] = useState<string | null>(
        null,
    );

    const [joinCodeState, setJoinCodeState] = useState<{
        code: string | null;
        resolvedId: string | null;
    }>({code: null, resolvedId: null});
    const joinCodeLoading = joinCodeState.resolvedId !== neighbourhoodId;
    const [regeneratingJoinCode, setRegeneratingJoinCode] = useState(false);
    

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

        fetchJoinRequests(neighbourhoodId, controller.signal)
            .then((data) => {
                if (!mountedRef.current) return;

                dispatch({
                    type: "FETCH_SUCCESS",
                    payload: data,
                });
            })
            .catch((err: unknown) => {
                if (!mountedRef.current) return;

                if (
                    err instanceof DOMException &&
                    err.name === "AbortError"
                ) {
                    return;
                }

                const message =
                    err instanceof ApiError
                        ? err.message
                        : err instanceof Error
                            ? err.message
                            : "Failed to load join requests.";

                dispatch({
                    type: "FETCH_ERROR",
                    payload: message,
                });
            });

        return () => controller.abort();
    }, [fetchTick, neighbourhoodId]);


    useEffect(() => {
        const controller = new AbortController();

        fetchJoinCodeRequest(neighbourhoodId)
            .then((data) => {
                if (!mountedRef.current) return;

                setJoinCodeState({
                    code: data.join_code,
                    resolvedId: neighbourhoodId,
                });
            })
            .catch((err: unknown) => {
                if (!mountedRef.current) return;

                if (
                    err instanceof DOMException &&
                    err.name === "AbortError"
                ) {
                    return;
                }

                setActionError(
                    err instanceof ApiError
                        ? err.message
                        : err instanceof Error
                            ? err.message
                            : "Failed to load join code.",
                );
                setJoinCodeState((s) => ({...s, resolvedId: neighbourhoodId}));
            });

        return () => controller.abort();
    }, [neighbourhoodId]);


    const handleApprove = useCallback(async (id: string) => {
        setActionError(null);

        try {
            const updated = await resolveJoinRequest(id , "APPROVE");

            dispatch({
                type: "UPDATE_REQUEST",
                payload: updated,
            });
        } catch (err) {
            setActionError(
                err instanceof ApiError
                    ? err.message
                    : err instanceof Error
                        ? err.message
                        : "Failed to approve join request.",
            );
        }
    }, [adminProperty]);

    const handleDeny = useCallback(async (id: string) => {
        setActionError(null);

        try {
            const updated = await resolveJoinRequest(id, "DENY");

            dispatch({
                type: "UPDATE_REQUEST",
                payload: updated,
            });
        } catch (err) {
            setActionError(
                err instanceof ApiError
                    ? err.message
                    : err instanceof Error
                        ? err.message
                        : "Failed to deny join request.",
            );
        }
    }, [adminProperty]);

    const filteredRequests = useMemo(() => {
        if (activeFilter === "ALL") {
            return requests;
        }

        return requests.filter(
            (request) => request.status === activeFilter,
        );
    }, [requests, activeFilter]);

    const handleRegenerateJoinCode = useCallback(async () => {
        setActionError(null);
        setRegeneratingJoinCode(true);

        try {
            const data = await regenerateJoinCodeRequest(neighbourhoodId);

            setJoinCodeState({
                code: data.join_code,
                resolvedId: neighbourhoodId,
            });
        } catch (err) {
            setActionError(
                err instanceof ApiError
                    ? err.message
                    : err instanceof Error
                        ? err.message
                        : "Failed to regenerate join code.",
            );
        } finally {
            setRegeneratingJoinCode(false);
        }
    }, [neighbourhoodId]);


    const pendingCount = requests.filter(
        (request) => request.status === "PENDING",
    ).length;

    if (!userContextLoading && !adminProperty) {
        return (
            <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
                <div className="mx-auto max-w-5xl">
                    <p className="text-sm text-brand-ash">
                        You don&apos;t have admin access to this neighbourhood.
                    </p>
                </div>
            </main>
        )
    }

    return (
        <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
            <div className="mx-auto max-w-5xl">
                <header className="flex flex-col gap-5 border-b border-border pb-7 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <p className="text-sm text-brand-green">
                            Neighbourhood management
                        </p>

                        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                            Join requests
                        </h1>

                        <p className="mt-2 max-w-xl text-sm leading-relaxed text-brand-ash">
                            Review requests from property owners who want to
                            join this neighbourhood.
                        </p>
                    </div>
                    
                    <div className="flex items-center gap-8">
                        <div>
                            <p className="text-xs uppercase tracking-wider text-brand-ash/60">
                                Join code
                            </p>

                            <div className="mt-1 flex items-center gap-2">
                                {joinCodeLoading ? (
                                    <Loader2 className="size-4 animate-spin text-brand-green" />
                                ) : (
                                    <>
                                        <code className="rounded-md bg-brand-slate px-2.5 py-1 font-mono text-sm font-medium tracking-widest text-brand-frost">
                                            {joinCodeState.code ?? "Unavailable"}
                                        </code>

                                        <button
                                            type="button"
                                            onClick={handleRegenerateJoinCode}
                                            disabled={
                                                regeneratingJoinCode || !joinCodeState.code
                                            }
                                            className="inline-flex size-7 items-center justify-center rounded-md text-brand-ash/70 transition-colors hover:bg-brand-slate hover:text-brand-frost disabled:cursor-not-allowed disabled:opacity-40"
                                            title="Regenerate join code"
                                        >
                                            {regeneratingJoinCode ? (
                                                <Loader2 className="size-3.5 animate-spin" />
                                            ) : (
                                                <RefreshCw className="size-3.5" />
                                            )}
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>

                        <div className="text-sm text-brand-ash">
                            <span className="font-medium text-brand-frost">
                                {pendingCount}
                            </span>{" "}
                            pending
                        </div>
                    </div>
                </header>

                <section className="pt-7">
                    {error && (
                        <ErrorBanner
                            message={error}
                            onDismiss={() =>
                                dispatch({ type: "DISMISS_ERROR" })
                            }
                        />
                    )}

                    {actionError && (
                        <ErrorBanner
                            message={actionError}
                            onDismiss={() => setActionError(null)}
                        />
                    )}

                    <div className="flex flex-col gap-4 border-b border-border pb-3 sm:flex-row sm:items-end sm:justify-between">
                        <div
                            className="flex items-center gap-5"
                            role="tablist"
                            aria-label="Filter join requests"
                        >
                            {(
                                [
                                    "PENDING",
                                    "APPROVED",
                                    "DENIED",
                                    "ALL",
                                ] as FilterValue[]
                            ).map((filter) => {
                                const isActive =
                                    activeFilter === filter;

                                const count =
                                    filter === "ALL"
                                        ? requests.length
                                        : requests.filter(
                                              (request) =>
                                                  request.status === filter,
                                          ).length;

                                return (
                                    <button
                                        key={filter}
                                        type="button"
                                        role="tab"
                                        aria-selected={isActive}
                                        onClick={() =>
                                            setActiveFilter(filter)
                                        }
                                        className={[
                                            "relative pb-3 text-sm transition-colors",
                                            isActive
                                                ? "font-medium text-brand-frost"
                                                : "text-brand-ash hover:text-brand-ash",
                                        ].join(" ")}
                                    >
                                        {STATUS_LABELS[filter]}

                                        <span className="ml-1.5 text-xs text-brand-ash/60">
                                            {count}
                                        </span>

                                        {isActive && (
                                            <span className="absolute inset-x-0 bottom-0 h-px bg-brand-green" />
                                        )}
                                    </button>
                                );
                            })}
                        </div>

                        <button
                            type="button"
                            onClick={() =>
                                setFetchTick((current) => current + 1)
                            }
                            disabled={loading}
                            className="inline-flex h-8 items-center gap-2 self-start rounded-md px-2 text-sm text-brand-ash transition-colors hover:bg-brand-slate hover:text-brand-frost disabled:cursor-not-allowed disabled:opacity-50 sm:self-auto"
                        >
                            {loading ? (
                                <Loader2 className="size-3.5 animate-spin" />
                            ) : (
                                <RefreshCw className="size-3.5" />
                            )}

                            Refresh
                        </button>
                    </div>

                    <section
                        aria-label="Join request list"
                        aria-live="polite"
                        className="pt-4"
                    >
                        {loading ? (
                            <div className="flex items-center justify-center py-20">
                                <Loader2 className="size-5 animate-spin text-brand-green" />
                            </div>
                        ) : filteredRequests.length === 0 ? (
                            <EmptyState filter={activeFilter} />
                        ) : (
                            <div className="space-y-2">
                                {filteredRequests.map((request) => (
                                    <RequestCard
                                        key={request.id}
                                        request={request}
                                        onApprove={handleApprove}
                                        onDeny={handleDeny}
                                    />
                                ))}
                            </div>
                        )}
                    </section>
                </section>
            </div>
        </main>
    );
}