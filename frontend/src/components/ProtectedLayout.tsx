"use client";

import {useRequireAuth} from "@/hooks/useRequireAuth";
import {Spinner} from "@/components/ui/spinner" 

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
    const { loading } = useRequireAuth();

    if (loading) {
        return <Spinner className="h-5 w-5 animate-spin" />;
    }

    return <>{children}</>;
}