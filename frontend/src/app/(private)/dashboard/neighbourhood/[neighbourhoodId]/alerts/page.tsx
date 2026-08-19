"use client";

import AlertsPage from "./AlertsPage"; // move your current component here
import { useParams } from "next/navigation";

export default function AlertPage() {
    const { neighbourhoodId } = useParams<{ neighbourhoodId: string}>();
    return <AlertsPage neighbourhoodId={neighbourhoodId}/>
}