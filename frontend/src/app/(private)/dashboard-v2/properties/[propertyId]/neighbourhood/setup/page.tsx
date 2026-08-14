"use client"

import Link from "next/link";
import { useState } from "react";
import {
    ArrowLeft,
    MapPin,
} from "lucide-react";

export default function NeighbourhoodSetupPage() {
    const [neighbourhoodName, setNeighbourhoodName] = useState("");
    const [location, setLocation] = useState("");

    return (
        <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
            <div className="max-w-full">
                <Link href="/dashboard-v2" className="inline-flex items-center gap-2 text-sm text-white/45 transition-colors hover:text-white">
                    <ArrowLeft className="size-4" />
                    Back to property
                </Link>

                <header className="mt-8 border-b border-white/10 pb-7">
                    <p className="text-sm text-emerald-400">
                        Neighbourhood setup
                    </p>

                    <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                        Create a neighbourhood
                    </h1>

                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/50">
                        Start a neighbourhood from this property. You can add 
                        neighbouring properties and residents after setup.
                    </p>
                </header>

                <section className="border-b border-white/10 py-6">
                    <p className="text-xs font-medium uppercase tracking-wider text-white/40">
                        Starting property
                    </p>

                    <div className="mt-3 flex items-start gap-3">
                        <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-emerald-500/10">
                            <MapPin className="size-4 text-emerald-400" />
                        </div>

                        <div>
                            <p className="text-sm font-medium text-white">
                                1332 Brook Street
                            </p>

                            <p className="mt-2 text-xs text-white/40">
                                This property will become the first property in
                                the new neighbourhood.
                            </p>
                        </div>
                    </div>
                </section>

                <section className="py-7">
                    <div className="mb-5">
                        <h2 className="text-base font-semibold text-white">
                            Neighbourhood details
                        </h2>

                        <p className="mt-1 text-sm text-white/45">
                            Choose a name residents will recognise.
                        </p>
                    </div>

                    <div className="space-y-5">
                        <div>
                            <label
                                htmlFor="neighbourhood-name"
                                className="text-sm font-medium text-white"
                            >
                                Neighbourhood name
                            </label>

                            <input
                                id="neighbourhood-name"
                                value={neighbourhoodName}
                                onChange={(event) =>
                                    setNeighbourhoodName(event.target.value)
                                }
                                placeholder="e.g. Brook Street Residents"
                                className="mt-2 h-10 w-full rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-emerald-500/60"
                            />

                            <p className="mt-2 text-xs text-white/40">
                                This name will appear in resident workspaces and
                                neighbourhood communications.
                            </p>
                        </div>

                        <div>
                            <label
                                htmlFor="neighbourhood-location"
                                className="text-sm font-medium text-white"
                            >
                                Location
                            </label>

                            <input
                                id="neighbourhood-location"
                                value={location}
                                onChange={(event) =>
                                    setLocation(event.target.value)
                                }
                                placeholder="e.g. Brooklyn"
                                className="mt-2 h-10 w-full rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-emerald-500/60"
                            />
                        </div>
                    </div>
                </section>

                <section className="border-t border-white/10 pt-6">
                    <div className="flex items-start gap-3">
                        <p className="text-sm leading-relaxed text-white/50">
                            You will become the first neighbourhood administrator.
                            You can then invite residents and review join requests.                        
                        </p>
                    </div>

                    <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                        <Link
                            href="/dashboard-v2"
                            className="inline-flex h-9 items-center justify-center rounded-md px-3.5 text-sm font-medium text-white/60 transition-colors hover:bg-white/5 hover:text-white"
                        >
                            Cancel
                        </Link>

                        <button
                            type="button"
                            disabled={!neighbourhoodName.trim() || !location.trim()}
                            className="inline-flex h-9 items-center justify-center rounded-md bg-emerald-500 px-3.5 text-sm font-medium text-black transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-500/30 disabled:text-black/50"
                        >
                            Create neighbourhood
                        </button>
                    </div>
                </section>
            </div>
        </main>
    )
}