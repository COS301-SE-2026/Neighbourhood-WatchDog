"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
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
        <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
            <div className="mx-auto max-w-3xl">
                <Link
                    href={`/dashboard/properties/${propertyId}`}
                    className="inline-flex items-center gap-2 text-sm text-brand-ash transition-colors hover:text-brand-frost"
                >
                    <ArrowLeft className="size-4" />
                    Back to property
                </Link>

                <header className="mt-8 border-b border-border pb-7">
                    <p className="text-sm text-brand-green">Property setup</p>
                    <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                        Connect an edge agent
                    </h1>
                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-brand-ash">
                        Pair {property.address} with an edge agent to enable camera monitoring.
                    </p>
                </header>

                <section className="py-7">
                    <div className="rounded-2xl border border-border bg-card p-6">
                        <PairAgent propertyId={property.id} propertyAddress={property.address} />
                    </div>
                </section>
            </div>
        </main>
    );
}
