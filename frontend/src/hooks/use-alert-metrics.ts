"use client";
import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib/api/client";


export interface AlertMetricItem {
    alert_id: string;
    camera_id: string;
    status: string; //"ACKNOWLEDGED, RESOLVED, PENDING"
    response_seconds: number | null;
    acknowledged_by: string | null;
    created_at: string;

}

export interface AlertMetrics {

    total_alerts: number;
    acknowledged_count: number;
    pending_count: number;
    average_response_seconds: number | null;
    items: AlertMetricItem[];

}

export function useAlertMetrics(
    neighbourhoodId: string,
    cameraId?: string,
    officerId?: string

) {

    const [metrics, setMetrics] = useState<AlertMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);


    const fetchMetrics = useCallback(async () => {
        setLoading(true);
        
        setError(null);

        try{
            const params = new URLSearchParams({ neighbourhood_id: neighbourhoodId});
            
            if (cameraId) params.set("camera_id", cameraId);
            if (officerId) params.set("officer_id", officerId);

            const data = await apiCall<AlertMetrics>(`/alerts/metrics?${params}`);
            setMetrics(data);

        }
        catch (e) {
            setError(`Failed to load metrics: ${e}`);
        }
        finally {
            setLoading(false);
        }
    }, [neighbourhoodId, cameraId, officerId]);


    useEffect(() => {
        const timeoutId = setTimeout(() => {
            void fetchMetrics();
        }, 0);

        return () => clearTimeout(timeoutId);

    }, [fetchMetrics]);


    return { 
        metrics, 
        loading, 
        error, 
        refetch: fetchMetrics
    };

}
