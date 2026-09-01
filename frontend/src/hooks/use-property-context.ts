"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Building2, House, type LucideIcon } from "lucide-react";
import { useUserContext } from "./use-user-context";
import type { CurrentUserContextRes, CurrentUserProperty } from "@/lib/validators/user";

export type ContextRole = "Resident" | "Neighbourhood Admin" | null;

export type PropertyContext = {
    id: string;
    propertyId: string;
    neighbourhoodId: string | null;
    name: string;
    address: string;
    role: ContextRole;
    icon: LucideIcon;
    canRequestNeighbourhoodJoin: boolean;
}
function deriveContextRole(property: CurrentUserProperty): ContextRole {
    if (property.neighbourhood === null) return null;
    return property.is_admin ? "Neighbourhood Admin" : "Resident";
}

function buildPropertyContexts(
    data: CurrentUserContextRes | undefined
): PropertyContext[] {
    if (!data) return [];

    return data.properties.map((property) => ({
        id: property.id,
        propertyId: property.id,
        neighbourhoodId: property.neighbourhood?.id ?? null,
        name: property.neighbourhood?.name ?? property.address,
        address: property.address,
        role: deriveContextRole(property),
        icon: property.neighbourhood ? Building2 : House,
        canRequestNeighbourhoodJoin: property.neighbourhood === null,
    }));
}

const LAST_PROPERTY_KEY = "lastActivePropertyId";

export function usePropertyContext() {
    const { data, isLoading } = useUserContext();
    const params = useParams<{ propertyId?: string }>();
    const router = useRouter();

    const contexts = useMemo(() => buildPropertyContexts(data), [data]);
    const urlPropertyId = params?.propertyId;

    const [fallbackId, setFallbackId] = useState<string | null>(null);
    useEffect(() => {
        if (!urlPropertyId) {
            // eslint-disable-next-line react-hooks/set-state-in-effect -- reading localStorage must happen client-side, after hydration to avoid SSR  mismatch 
            setFallbackId(localStorage.getItem(LAST_PROPERTY_KEY));
        }
    }, [urlPropertyId]);

    const activeId = urlPropertyId ?? fallbackId ?? contexts[0]?.id ?? null;

    const activeContext = useMemo(
        () => contexts.find((c) => c.id === activeId) ?? contexts[0] ?? null,
        [contexts, activeId],
    );

    function selectContext(context: PropertyContext) {
        localStorage.setItem(LAST_PROPERTY_KEY, context.id);
        router.push(`/dashboard/properties/${context.propertyId}/cameras`);
    }

    return { contexts, activeContext, isLoading, selectContext };
}
