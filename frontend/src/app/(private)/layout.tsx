"use client";

import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function ProtectedLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    useRequireAuth();

    return <>{children}</>;
}