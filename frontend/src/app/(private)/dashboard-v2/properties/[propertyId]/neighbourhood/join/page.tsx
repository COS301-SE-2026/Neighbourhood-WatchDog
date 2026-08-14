"use client";

import { useState, type ElementType, type FormEvent } from "react";
import {
    Check,
    ChevronRight,
    Clock,
    Loader2,
    ShieldCheck,
    XCircle,
} from "lucide-react";

import {
    submitJoinRequest,
    ApiError,
} from "@/lib/api/neighbourhoodJoin";
import type { JoinRequest } from "@/components/shared/RequestCard";

type RequestState =
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "pending"; request: JoinRequest }
    | { kind: "error"; message: string };

function StatusRow({
    icon: Icon,
    label,
    state,
}: {
    icon: ElementType;
    label: string;
    state: "complete" | "current" | "upcoming";
}) {
    const iconClassName =
        state === "complete"
            ? "bg-emerald-500/15 text-emerald-400"
            : state === "current"
                ? "bg-white/10 text-white/65"
                : "bg-white/[0.04] text-white/25";

    const labelClassName =
        state === "complete"
            ? "text-white"
            : state === "current"
                ? "text-white/65"
                : "text-white/30";

    return (
        <div className="flex items-center gap-3">
            <div
                className={`flex size-6 shrink-0 items-center justify-center rounded-full ${iconClassName}`}
            >
                <Icon className="size-3.5" />
            </div>

            <span className={`text-sm ${labelClassName}`}>{label}</span>
        </div>
    );
}

function PendingState({ request }: { request: JoinRequest }) {
    return (
        <section
            className="max-w-xl"
            role="status"
            aria-live="polite"
        >
            <div className="border-b border-white/10 pb-7">
                <div className="flex size-10 items-center justify-center rounded-md bg-emerald-500/10">
                    <Clock className="size-5 text-emerald-400" />
                </div>

                <p className="mt-5 text-sm text-emerald-400">
                    Request submitted
                </p>

                <h1 className="mt-1 text-2xl font-semibold tracking-tight text-white">
                    Awaiting review
                </h1>

                <p className="mt-3 max-w-lg text-sm leading-relaxed text-white/50">
                    A neighbourhood administrator will review your request.
                    Once approved, this property will gain access to the
                    neighbourhood workspace and alerts.
                </p>
            </div>

            <div className="py-6">
                <p className="text-xs font-medium uppercase tracking-wider text-white/40">
                    Request progress
                </p>

                <div className="mt-4 space-y-4">
                    <StatusRow
                        icon={Check}
                        label="Join request submitted"
                        state="complete"
                    />

                    <StatusRow
                        icon={Clock}
                        label="Administrator review"
                        state="current"
                    />

                    <StatusRow
                        icon={ShieldCheck}
                        label="Neighbourhood access granted"
                        state="upcoming"
                    />
                </div>
            </div>

            <div className="border-t border-white/10 pt-5">
                <p className="text-xs text-white/35">
                    Request reference
                </p>

                <p className="mt-1 break-all font-mono text-xs text-white/55">
                    {request.id}
                </p>
            </div>
        </section>
    );
}

function JoinForm({
    onSubmit,
    loading,
    error,
}: {
    onSubmit: (code: string) => void;
    loading: boolean;
    error: string | null;
}) {
    const [code, setCode] = useState("");

    const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (code.trim()) {
            onSubmit(code.trim());
        }
    };

    return (
        <form
            onSubmit={handleSubmit}
            noValidate
            className="max-w-xl"
        >
            <div className="border-b border-white/10 pb-7">
                <label
                    htmlFor="join-code"
                    className="text-sm font-medium text-white"
                >
                    Join code
                </label>

                <p
                    id="join-code-hint"
                    className="mt-1 text-sm leading-relaxed text-white/45"
                >
                    Enter the code provided by a neighbourhood administrator.
                </p>

                <input
                    id="join-code"
                    type="text"
                    value={code}
                    onChange={(event) =>
                        setCode(event.target.value.toUpperCase())
                    }
                    placeholder="e.g. NORTH-5F3A"
                    maxLength={32}
                    autoComplete="off"
                    autoCapitalize="characters"
                    spellCheck={false}
                    disabled={loading}
                    aria-invalid={Boolean(error)}
                    aria-describedby={
                        error ? "join-code-error" : "join-code-hint"
                    }
                    className={[
                        "mt-4 h-10 w-full rounded-md border bg-zinc-950 px-3",
                        "font-mono text-sm tracking-[0.12em] text-white",
                        "outline-none placeholder:text-white/20",
                        "focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/40",
                        "disabled:cursor-not-allowed disabled:opacity-50",
                        error
                            ? "border-red-500/70 focus:border-red-500 focus:ring-red-500/40"
                            : "border-white/10",
                    ].join(" ")}
                />

                {error && (
                    <p
                        id="join-code-error"
                        role="alert"
                        className="mt-2 flex items-center gap-1.5 text-xs text-red-300"
                    >
                        <XCircle className="size-3.5 shrink-0" />
                        {error}
                    </p>
                )}
            </div>

            <div className="flex items-center justify-between gap-4 pt-5">
                <p className="max-w-sm text-xs leading-relaxed text-white/35">
                    Your request is sent for the currently selected property.
                </p>

                <button
                    type="submit"
                    disabled={!code.trim() || loading}
                    className="inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-md bg-emerald-500 px-3.5 text-sm font-medium text-black transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-500/30 disabled:text-black/50"
                >
                    {loading ? (
                        <>
                            <Loader2 className="size-4 animate-spin" />
                            Sending
                        </>
                    ) : (
                        <>
                            Request to join
                            <ChevronRight className="size-4" />
                        </>
                    )}
                </button>
            </div>
        </form>
    );
}

export default function JoinNeighbourhoodPage() {
    const [state, setState] = useState<RequestState>({
        kind: "idle",
    });

    async function handleSubmit(code: string) {
        setState({ kind: "loading" });

        try {
            const request = await submitJoinRequest(code);

            setState({
                kind: "pending",
                request,
            });
        } catch (error) {
            const message =
                error instanceof ApiError
                    ? error.message
                    : error instanceof Error
                        ? error.message
                        : "Could not send join request.";

            setState({
                kind: "error",
                message,
            });
        }
    }

    if (state.kind === "pending") {
        return (
            <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
                <div className="mx-auto max-w-3xl">
                    <PendingState request={state.request} />
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
            <div className="mx-auto max-w-3xl">
                <header className="border-b border-white/10 pb-7">
                    <p className="text-sm text-emerald-400">
                        Neighbourhood
                    </p>

                    <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                        Join a neighbourhood
                    </h1>

                    <p className="mt-3 max-w-xl text-sm leading-relaxed text-white/50">
                        Use a neighbourhood join code to request access for
                        your selected property. Once approved, you will be able
                        to view neighbourhood alerts and activity.
                    </p>
                </header>

                <section className="py-7">
                    <div className="mb-5">
                        <h2 className="text-base font-semibold text-white">
                            Enter join code
                        </h2>
                    </div>

                    <JoinForm
                        onSubmit={handleSubmit}
                        loading={state.kind === "loading"}
                        error={
                            state.kind === "error"
                                ? state.message
                                : null
                        }
                    />
                </section>
            </div>
        </main>
    );
}