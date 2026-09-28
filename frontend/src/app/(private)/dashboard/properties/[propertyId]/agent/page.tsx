"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useUserContext } from "@/hooks/use-user-context";
import PairAgent from "@/components/property-components/PairAgent";

export default function ConnectAgentPage() {
    const { propertyId } = useParams<{ propertyId: string }>();
    const { data: userContext, isLoading } = useUserContext();

    const property = userContext?.properties.find((p) => p.id === propertyId);

    if (isLoading) {
        return (
            <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
                <p className="text-sm text-brand-ash">Loading property...</p>
            </main>
        );
    }

    if (!property) {
        return (
            <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
                <p className="text-sm text-brand-ash">Property not found.</p>
            </main>
        );
    }

    return (
        <main className="min-h-full bg-brand-void px-4 py-5 text-brand-frost sm:px-6 md:px-8">
            <div className="mx-auto max-w-4xl">
                <header className="border-b border-border pb-5">
                    <p className="text-sm text-brand-green">
                        Property setup
                    </p>

                    <h1 className="mt-1.5 text-2xl font-semibold tracking-tight">
                        Connect an edge agent
                    </h1>

                    <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-brand-ash">
                        Pair {property.address} with an edge agent to enable camera monitoring.
                    </p>
                </header>

                <section className="py-5">
                    <div className="rounded-2xl border border-border bg-card p-4 sm:p-5">
                        <PairAgent
                            propertyId={property.id}
                            propertyAddress={property.address}
                        />
                    </div>
                </section>
            </div>
        </main>
    );
}
