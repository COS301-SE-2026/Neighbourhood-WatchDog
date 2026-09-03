"use client";

import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AuthProvider from "@/lib/auth/auth-context";

export function Providers({ children }: { children: React.ReactNode}) {
    const [queryClient] = useState(
        () => 
            new QueryClient({
            defaultOptions : ({
                queries: {
                    staleTime: 5 * 60 * 1000,
                    refetchOnWindowFocus: false,
                    refetchOnReconnect: true,
                    retry: 1
                }
            })
        }
    ));

    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>{children}</AuthProvider>
        </QueryClientProvider>
    )
}