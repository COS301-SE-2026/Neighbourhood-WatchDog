"use client";

import { useParams } from "next/navigation";
import { Loader2, Users } from "lucide-react";

import { useUserContext } from "@/hooks/use-user-context";

export default function MembersPage() {
    const { neighbourhoodId } = useParams<{neighbourhoodId: string}>();

    const {
        data: userContext,
        isLoading: userContextLoading,
    } = useUserContext();

    const isNeighbourhoodAdmin = Boolean(
        userContext?.properties.some(
            (property) =>
                property.neighbourhood?.id === neighbourhoodId &&
                property.neighbourhood?.role === "NEIGHBOURHOOD_ADMIN",
        ),
    );

    if (userContextLoading) {
        return (
            <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
                <div className="mx-auto flex max-w-5xl items-center justify-center py-20">
                    <Loader2 className="size-5 animate-spin text-emerald-400" />
                </div>
            </main>
        );
    }

    if (!isNeighbourhoodAdmin) {
        return (
            <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
                <div className="mx-auto max-w-5xl">
                    <p className="text-sm text-white/60">
                        You don&apos;t have admin access to this neighbourhood.
                    </p>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
            <div className="mx-auto max-w-5xl">
                <header className="border-b border-white/10 pb-7">
                    <p className="text-sm text-emerald-400">
                        Neighbourhood management
                    </p>

                    <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                        Members
                    </h1>

                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/50">
                        View members of this neighbourhood and manage their roles.
                    </p>
                </header>

                <section className="pt-7">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                        <Users className="size-4 text-emerald-400" />

                        <div>
                            <h2 className="text-sm font-medium text-white">
                                Neighbourhood members
                            </h2>

                            <p className="mt-1 text-sm text-white/40">
                                Members and their current roles will appear here.
                            </p>
                        </div>
                    </div>
                </section>
            </div>
        </main>
    );
}
