"use client";

import { useEffect} from "react"; //use state
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";

export function useRequireAuth() {
    const router = useRouter();
    const {isLoading, isLoggedIn} = useAuth();

    useEffect(() => {
        if (!isLoading && !isLoggedIn) {
            router.replace("/auth/login");
        }
    }, [isLoading, isLoggedIn, router]);

    return { isLoading, isLoggedIn };
}