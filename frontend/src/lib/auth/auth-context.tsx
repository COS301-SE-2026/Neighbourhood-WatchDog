"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { AUTH_EVENT, getStoredUser, type StoredUser } from "./cognito";

interface AuthContextValue {
    user: StoredUser | null;
    isLoggedIn: boolean;
    isLoading: boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);


export default function AuthProvider({children}: {children: ReactNode}) {
    const [user, setUser] = useState<StoredUser | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const sync = () => setUser(getStoredUser());

        /* eslint-disable react-hooks/set-state-in-effect -- reading localStorage must happen client-side, after hydration to avoid SSR  mismatch */
        sync();
        setIsLoading(false);
        /* eslint-enable react-hooks/set-state-in-effect */

        window.addEventListener(AUTH_EVENT, sync);
        return () => window.removeEventListener(AUTH_EVENT, sync);
    }, []);

    return(
        <AuthContext.Provider value={{user, isLoggedIn: !user, isLoading}}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
    return ctx;
}