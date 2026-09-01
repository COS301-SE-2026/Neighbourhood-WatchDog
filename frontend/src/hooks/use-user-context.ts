import { useQuery } from "@tanstack/react-query";

import { fetchMyContext } from "@/lib/api/user-context";
import type { CurrentUserContextRes } from "@/lib/validators/user";

export function useUserContext() {
    return useQuery<CurrentUserContextRes>({
        queryKey: ["userContext"],
        queryFn: fetchMyContext,
        staleTime: 60_000,
    });
}