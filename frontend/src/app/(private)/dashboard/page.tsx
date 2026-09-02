"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { usePropertyContext } from "@/hooks/use-property-context";
import { CreatePropertyDialog } from "@/components/property-components/create-property-dialogue";

export default function DashboardV2Page() {
    const { contexts, isLoading } = usePropertyContext();
    const [dialogOpen, setDialogOpen] = useState(false);

    if (isLoading) {
        return <main className="flex-1" />;
    }

    if (contexts.length > 0) {
        return <main className="flex-1" />;
    }

    return (
        <>
            <main className="flex flex-1 items-center justify-center px-6 py-10">
                <div className="max-w-md text-center">
                    <h1 className="text-xl font-semibold text-white">
                        Create your first property
                    </h1>

                    <p className="mt-2 text-sm leading-6 text-white/50">
                        Add a property to start connecting cameras and
                        monitoring alerts.
                    </p>

                    <button
                        type="button"
                        onClick={() => setDialogOpen(true)}
                        className="mt-5 inline-flex items-center gap-2 rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-emerald-400"
                    >
                        <Plus className="size-4" />
                        Add property
                    </button>
                </div>
            </main>

            <CreatePropertyDialog
                open={dialogOpen}
                onOpenChange={setDialogOpen}
                onPropertyAdded={() => {
                    setDialogOpen(false);
                    window.location.reload();
                }}
            />
        </>
    );
}
