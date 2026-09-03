"use client"

import Link from "next/link";
import { FormEvent, useState } from "react";
import {
    ArrowLeft,
    Loader2,
    MapPin,
} from "lucide-react";

import { addNeighbourhood } from "@/lib/api/neighbourhood";
import { usePropertyContext } from "@/hooks/use-property-context";
import { toast } from "sonner";

export default function NeighbourhoodSetupPage() {

    const { activeContext, isLoading: isLoadingProperty} = usePropertyContext();

    const [neighbourhoodName, setNeighbourhoodName] = useState("");
    const [location, setLocation] = useState("");
    const [isCreating, setIsCreating] = useState(false);

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!activeContext) {
            toast.error("No property is currently selected.");
            return;
        }

        if (!neighbourhoodName.trim() || !location.trim()) {
            return;
        }

        setIsCreating(true);

        try {
            const neighbourhood = await addNeighbourhood({
                name: neighbourhoodName.trim(),
                location: location.trim(),
                property_id: activeContext.propertyId,
            });

            toast.success("Neighbourhood created");

            console.log("Created neighbourhood:", neighbourhood);

            window.location.href = `/dashboard/properties/${activeContext.propertyId}/cameras`;
        } catch (error) {
            console.error("Failed to create neighbourhood", error);

            toast.error(
                error instanceof Error
                    ? error.message
                    : "Failed to create neighbourhood.",
            );
        } finally {
            setIsCreating(false);
        }
    };

    if (isLoadingProperty) {
        return (
            <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
                <div className="flex min-h-64 items-center justify-center">
                    <Loader2 className="size-5 animate-spin text-brand-green" />
                </div>
            </main>
        );
    }

    if (!activeContext) {
        return (
            <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
                <div className="mx-auto max-w-3xl">
                    <Link
                        href="/dashboard"
                        className="inline-flex items-center gap-2 text-sm text-brand-ash transition-colors hover:text-brand-frost"
                    >
                        <ArrowLeft className="size-4" />
                        Back to property
                    </Link>

                    <header className="mt-8 border-b border-border pb-7">
                        <p className="text-sm text-brand-green">
                            Neighbourhood setup
                        </p>

                        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                            Create a neighbourhood
                        </h1>

                        <p className="mt-2 max-w-xl text-sm leading-relaxed text-brand-ash">
                            Select a property before creating a neighbourhood.
                        </p>
                    </header>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
            <div className="max-w-full">
                <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-brand-ash transition-colors hover:text-brand-frost">
                    <ArrowLeft className="size-4" />
                    Back to property
                </Link>

                <header className="mt-8 border-b border-border pb-7">
                    <p className="text-sm text-brand-green">
                        Neighbourhood setup
                    </p>

                    <h1 className="mt-2 text-2xl font-semibold tracking-tight text-brand-frost">
                        Create a neighbourhood
                    </h1>

                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-brand-ash">
                        Start a neighbourhood from this property. You can add 
                        neighbouring properties and residents after setup.
                    </p>
                </header>

                <section className="border-b border-border py-6">
                    <p className="text-xs font-medium uppercase tracking-wider text-brand-ash/70">
                        Starting property
                    </p>

                    <div className="mt-3 flex items-start gap-3">
                        <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-brand-green/10">
                            <MapPin className="size-4 text-brand-green" />
                        </div>

                        <div>
                            <p className="text-sm font-medium text-brand-frost">
                                {activeContext.address}
                            </p>

                            <p className="mt-2 text-xs text-brand-ash/70">
                                This property will become the first property in
                                the new neighbourhood.
                            </p>
                        </div>
                    </div>
                </section>

                <form onSubmit={handleSubmit}>
                    <section className="py-7">
                        <div className="mb-5">
                            <h2 className="text-base font-semibold text-brand-frost">
                                Neighbourhood details
                            </h2>
                            <p className="mt-1 text-sm text-brand-ash">
                                Choose a name residents will recognise.
                            </p>
                        </div>
                        <div className="space-y-5">
                            <div>
                                <label
                                    htmlFor="neighbourhood-name"
                                    className="text-sm font-medium text-brand-frost"
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
                                    className="mt-2 h-10 w-full rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-frost outline-none placeholder:text-brand-ash/60 focus:border-brand-green/60"
                                />
                                <p className="mt-2 text-xs text-brand-ash/70">
                                    This name will appear in resident workspaces and
                                    neighbourhood communications.
                                </p>
                            </div>
                            <div>
                                <label
                                    htmlFor="neighbourhood-location"
                                    className="text-sm font-medium text-brand-frost"
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
                                    className="mt-2 h-10 w-full rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-frost outline-none placeholder:text-brand-ash/60 focus:border-brand-green/60"
                                />
                            </div>
                        </div>
                    </section>
                    <section className="border-t border-border pt-6">
                        <div className="flex items-start gap-3">
                            <p className="text-sm leading-relaxed text-brand-ash">
                                You will become the first neighbourhood administrator.
                                You can then invite residents and review join requests.
                            </p>
                        </div>
                        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                            <Link
                                href="/dashboard"
                                className="inline-flex h-9 items-center justify-center rounded-md px-3.5 text-sm font-medium text-brand-ash transition-colors hover:bg-brand-slate hover:text-brand-frost"
                            >
                                Cancel
                            </Link>
                            <button
                                type="submit"
                                disabled={isCreating || !neighbourhoodName.trim() || !location.trim()}
                                className="inline-flex h-9 items-center justify-center rounded-md bg-brand-green px-3.5 text-sm font-medium text-brand-void transition-colors hover:bg-brand-green disabled:cursor-not-allowed disabled:bg-brand-green/30 disabled:text-brand-void/50"
                            >
                                {isCreating && (
                                        <Loader2 className="size-4 animate-spin" />
                                    )}
                                {isCreating
                                    ? "Creating..."
                                    : "Create neighbourhood"}
                            </button>
                        </div>
                    </section>
                </form>
            </div>
        </main>
    )
}