import { useQuery } from "@tanstack/react-query";

import { fetchMyContext } from "@/lib/api/user-context";
import type { CurrentUserContextRes } from "@/lib/validators/user";

export function useUserContext(enabled = true) {
    return useQuery<CurrentUserContextRes>({
        queryKey: ["userContext"],
        queryFn: fetchMyContext,
        enabled,
        staleTime: 5 * 60 * 1000,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true
    });
}