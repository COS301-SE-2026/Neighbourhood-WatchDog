"use client";

import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function ProtectedLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { loading } = useRequireAuth();

    if (loading) {
        return <div>Loading...</div>;
    }

    return <>{children}</>;
}