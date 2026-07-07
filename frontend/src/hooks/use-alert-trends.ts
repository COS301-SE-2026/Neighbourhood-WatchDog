"use client";
import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib/api/client";
import { string } from "zod";
import { tr } from "zod/locales";


export interface TrendBucket {

    period: string;
    total: number;
    by_type: Record<string, number>;
    by_camera: Record<string, number>;
}


export interface TrendData{

    buckets: TrendBucket[];
    trend_direction: "increasing" | "decreasing" | "stable";
    trend_percentage: number | null;
    total_alerts: number;
    date_from: string;
    date_to: string;

}


export function useAlertTrends (
    neighbourhoodId: string,
    startDate: string,
    endDate: string,
    groupBy: "day" | "week" | "month",
    incidentType?: string,
    cameraId?: string

) {
    const [data, setData] = useState<TrendData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);


    const fetchTrends = useCallback(async () => {

        setLoading(true);
        setError(null);
        try{
            const params = new URLSearchParams({
                neighbourhood_id: neighbourhoodId,
                group_by: groupBy,
                start_date: startDate,
                end_date: endDate

            });


            if (incidentType) params.set("incident_type", incidentType);
            if (cameraId) params.set("camera_id", cameraId);


            const result = await apiCall<TrendData>(`/alerts/trends?${params}`);

            setData(result);
        }
        catch (e){
            setError(`Failed to load trends: ${e}`);
        }
        finally {
            setLoading(false);
        }


    }, [neighbourhoodId, startDate, endDate, groupBy, incidentType, cameraId]);

    useEffect(() => {
        const id = setTimeout(() => {
            void fetchTrends();

        }, 0);

        return () => clearTimeout(id);
    }, [fetchTrends]);

    return { 
        data, 
        loading, 
        error,
        refetch: fetchTrends
    };
}
