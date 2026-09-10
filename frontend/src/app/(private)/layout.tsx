"use client";

import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function ProtectedLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { isLoading, isLoggedIn } = useRequireAuth();

    if (isLoading || !isLoggedIn) {
        return null;
    }

    return <>{children}</>;
}