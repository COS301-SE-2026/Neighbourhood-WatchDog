"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft, Clock, Gauge, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { usePropertyContext } from "@/hooks/use-property-context";
import { fetchNeighbourhoodRiskThreshold, updateNeighbourhoodRiskThreshold } from "@/lib/api/riskThreshold";

const THRESHOLD_BOUNDS = { lowMax: { min: 0, max: 100 }, mediumMax: { min: 0, max: 100 } };

export default function RiskThresholdPage() {
    const { activeContext, isLoading: isLoadingProperty } = usePropertyContext();
    const [lowMax, setLowMax] = useState("");
    const [mediumMax, setMediumMax] = useState("");
    const [updatedAt, setUpdatedAt] = useState<string | null>(null);
    const [isLoadingThreshold, setIsLoadingThreshold] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (!activeContext || activeContext.neighbourhoodId === null) {
            setIsLoadingThreshold(false);
            return;
        }
        const neighbourhoodId = activeContext.neighbourhoodId;
        (async () => {
            setIsLoadingThreshold(true);
            try {
                const { data } = await fetchNeighbourhoodRiskThreshold(neighbourhoodId);
                setLowMax(String(data.low_max));
                setMediumMax(String(data.medium_max));
                setUpdatedAt(data.updated_at);
            } catch (error) {
                toast.error(error instanceof Error ? error.message : "Failed to load risk threshold.");
            } finally {
                setIsLoadingThreshold(false);
            }
        })();
    }, [activeContext]);

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!activeContext || activeContext.neighbourhoodId === null) {
            toast.error("No neighbourhood is currently selected.");
            return;
        }
        const neighbourhoodId = activeContext.neighbourhoodId;

        if (!lowMax.trim() && !mediumMax.trim()) {
            toast.error("Enter at least one threshold.");
            return;
        }

        const lowValue = lowMax.trim() ? Number(lowMax) : undefined;
        const mediumValue = mediumMax.trim() ? Number(mediumMax) : undefined;

        if (lowValue !== undefined && (lowValue < THRESHOLD_BOUNDS.lowMax.min || lowValue > THRESHOLD_BOUNDS.lowMax.max)) {
            toast.error("Low risk max must be between 0 and 100.");
            return;
        }
        if (mediumValue !== undefined && (mediumValue < THRESHOLD_BOUNDS.mediumMax.min || mediumValue > THRESHOLD_BOUNDS.mediumMax.max)) {
            toast.error("Medium risk max must be between 0 and 100.");
            return;
        }
        if (lowValue !== undefined && mediumValue !== undefined && mediumValue <= lowValue) {
            toast.error("Medium risk max must be greater than low risk max.");
            return;
        }

        setIsSaving(true);
        try {
            const { data } = await updateNeighbourhoodRiskThreshold(neighbourhoodId, { low_max: lowValue, medium_max: mediumValue });
            setLowMax(String(data.low_max));
            setMediumMax(String(data.medium_max));
            setUpdatedAt(data.updated_at);
            toast.success("Risk thresholds updated");
        } catch (error) {
            toast.error(error instanceof Error ? error.message : "Failed to update risk threshold.");
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoadingProperty) {
        return (
            <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
                <div className="flex min-h-64 items-center justify-center">
                    <Loader2 className="size-5 animate-spin text-emerald-400" />
                </div>
            </main>
        );
    }

    if (!activeContext || activeContext.neighbourhoodId === null) {
        return (
            <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
                <div className="mx-auto max-w-3xl">
                    <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-white/45 transition-colors hover:text-white">
                        <ArrowLeft className="size-4" /> Back to neighbourhood
                    </Link>
                    <header className="mt-8 border-b border-white/10 pb-7">
                        <p className="text-sm text-emerald-400">Risk threshold</p>
                        <h1 className="mt-2 text-2xl font-semibold tracking-tight">Configure risk thresholds</h1>
                        <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/50">Select a neighbourhood before configuring risk thresholds.</p>
                    </header>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
            <div className="max-w-full">
                <Link href={`/dashboard/neighbourhood/${activeContext.neighbourhoodId}`} className="inline-flex items-center gap-2 text-sm text-white/45 transition-colors hover:text-white">
                    <ArrowLeft className="size-4" /> Back to neighbourhood
                </Link>

                <header className="mt-8 border-b border-white/10 pb-7">
                    <p className="text-sm text-emerald-400">Risk threshold</p>
                    <h1 className="mt-2 text-2xl font-semibold tracking-tight">Configure risk thresholds</h1>
                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/50">Set the score boundaries that classify events as low, medium, or high risk for this neighbourhood.</p>
                </header>

                <section className="border-b border-white/10 py-6">
                    <p className="text-xs font-medium uppercase tracking-wider text-white/40">Neighbourhood</p>
                    <div className="mt-3 flex items-start gap-3">
                        <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-emerald-500/10">
                            <Gauge className="size-4 text-emerald-400" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-white">{activeContext.name ?? "Current neighbourhood"}</p>
                            <p className="mt-2 text-xs text-white/40">Thresholds apply to all cameras and residents in this neighbourhood.</p>
                        </div>
                    </div>
                </section>

                {isLoadingThreshold ? (
                    <div className="flex min-h-40 items-center justify-center">
                        <Loader2 className="size-5 animate-spin text-emerald-400" />
                    </div>
                ) : (
                    <>
                        <section className="border-b border-white/10 py-6">
                            <p className="text-xs font-medium uppercase tracking-wider text-white/40">Current configuration</p>
                            <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
                                <div className="rounded-md border border-white/10 bg-zinc-950 px-4 py-3">
                                    <p className="text-xs text-white/40">Low risk max</p>
                                    <p className="mt-1 text-lg font-semibold text-white">{lowMax}</p>
                                </div>
                                <div className="rounded-md border border-white/10 bg-zinc-950 px-4 py-3">
                                    <p className="text-xs text-white/40">Medium risk max</p>
                                    <p className="mt-1 text-lg font-semibold text-white">{mediumMax}</p>
                                </div>
                            </div>
                            {updatedAt && (
                                <p className="mt-3 flex items-center gap-1.5 text-xs text-white/40">
                                    <Clock className="size-3.5" /> Last updated {new Date(updatedAt).toLocaleString()}
                                </p>
                            )}
                        </section>

                        <form onSubmit={handleSubmit}>
                            <section className="py-7">
                                <div className="mb-5">
                                    <h2 className="text-base font-semibold text-white">Update thresholds</h2>
                                    <p className="mt-1 text-sm text-white/45">Medium risk max must be greater than low risk max.</p>
                                </div>

                                <div className="space-y-5">
                                    <div>
                                        <label htmlFor="low-max" className="text-sm font-medium text-white">Low risk max</label>
                                        <input
                                            id="low-max" type="number" step="1"
                                            min={THRESHOLD_BOUNDS.lowMax.min} max={THRESHOLD_BOUNDS.lowMax.max}
                                            value={lowMax} onChange={(e) => setLowMax(e.target.value)}
                                            className="mt-2 h-10 w-full rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-emerald-500/60 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                        />
                                        <p className="mt-2 text-xs text-white/40">Scores at or below this value are classified as low risk.</p>
                                    </div>

                                    <div>
                                        <label htmlFor="medium-max" className="text-sm font-medium text-white">Medium risk max</label>
                                        <input
                                            id="medium-max" type="number" step="1"
                                            min={THRESHOLD_BOUNDS.mediumMax.min} max={THRESHOLD_BOUNDS.mediumMax.max}
                                            value={mediumMax} onChange={(e) => setMediumMax(e.target.value)}
                                            className="mt-2 h-10 w-full rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-emerald-500/60 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                        />
                                        <p className="mt-2 text-xs text-white/40">Scores above the low threshold and at or below this value are classified as medium risk.</p>
                                    </div>
                                </div>
                            </section>

                            <section className="border-t border-white/10 pt-6">
                                <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                                    <Link href={`/dashboard/neighbourhood/${activeContext.neighbourhoodId}`} className="inline-flex h-9 items-center justify-center rounded-md px-3.5 text-sm font-medium text-white/60 transition-colors hover:bg-white/5 hover:text-white">
                                        Cancel
                                    </Link>
                                    <button
                                        type="submit"
                                        disabled={isSaving || (!lowMax.trim() && !mediumMax.trim())}
                                        className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-emerald-500 px-3.5 text-sm font-medium text-black transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-500/30 disabled:text-black/50"
                                    >
                                        {isSaving && <Loader2 className="size-4 animate-spin" />}
                                        {isSaving ? "Saving..." : "Save thresholds"}
                                    </button>
                                </div>
                            </section>
                        </form>
                    </>
                )}
            </div>
        </main>
    );
}
