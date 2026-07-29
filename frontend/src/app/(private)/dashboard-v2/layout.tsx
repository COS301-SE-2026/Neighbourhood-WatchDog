import type { ReactNode } from "react";

export default function DashboardLayout({
    children,
}: {
    children: ReactNode;
}) {
    return (
        <div className="min-h-screen bg-background text-foreground">
            <main className="min-h-screen">
                {children}
            </main>
        </div>
    );
}