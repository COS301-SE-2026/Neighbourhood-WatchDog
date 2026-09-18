"use client"

import StatusToggle from "@/components/security-components/StatusLocation";
import { usePropertyContext } from "@/hooks/use-property-context";

export default function OfficerDashboard() {
    const { activeContext } = usePropertyContext()

    if (!activeContext?.neighbourhoodId) {
        return <p>No neighbourhood found for this property.</p>
    }

    return (
        <StatusToggle neighbourhoodId={activeContext.neighbourhoodId}/> 
    )
}