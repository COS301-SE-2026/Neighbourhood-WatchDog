"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useUserContext } from "@/hooks/use-user-context";
import type { CurrentUserSummary } from "@/lib/validators/user";
import {
  AUTH_EVENT,
  clearLegacyProfileStorage,
  clearSession,
  getAccessToken,
  refreshSession,
} from "./cognito";

interface AuthContextValue {
  user: CurrentUserSummary | null;
  isLoggedIn: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export default function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const queryClient = useQueryClient();
  const [sessionReady, setSessionReady] = useState(false);
  const [restoring, setRestoring] = useState(true);

  const profile = useUserContext(sessionReady && !restoring);

  useEffect(() => {
    let mounted = true;

    const syncSession = () => {
      const hasToken = Boolean(getAccessToken());

      if (!hasToken) {
        queryClient.removeQueries({ queryKey: ["userContext"] });
      }

      if (mounted) {
        setSessionReady(hasToken);
      }
    };

    window.addEventListener(AUTH_EVENT, syncSession);
    clearLegacyProfileStorage();

    const restore = async () => {
      try {
        await refreshSession();
      } catch {
        clearSession();
      } finally {
        if (mounted) {
          setRestoring(false);
        }
      }
    };

    void restore();

    return () => {
      mounted = false;
      window.removeEventListener(AUTH_EVENT, syncSession);
    };
  }, [queryClient]);

  const isLoading =
    restoring || (sessionReady && profile.isPending);

  return (
    <AuthContext.Provider
      value={{
        user: profile.data?.user ?? null,
        isLoggedIn: sessionReady,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
