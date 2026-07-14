"use client";
import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib/api/client";
import type { AlertFrequencyMetricsRes, NumberInPeriod } from "@/lib/validators/alerts";


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

function toTimePeriod(startDate: string, endDate: string): "WEEK" | "MONTH" | "THREE_MONTHS" | "SIX_MONTHS" | "YEAR" | "TOTAL" {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const days = Math.max(1, Math.ceil((end.getTime() - start.getTime()) / 86_400_000) + 1);

    if (days <= 7) return "WEEK";
    if (days <= 31) return "MONTH";
    if (days <= 92) return "THREE_MONTHS";
    if (days <= 183) return "SIX_MONTHS";
    if (days <= 366) return "YEAR";
    return "TOTAL";
}

function mapFrequencyResponse(
    buckets: NumberInPeriod[],
    startDate: string,
    endDate: string,
): TrendData {
    const totalAlerts = buckets.reduce((sum, bucket) => sum + bucket.count, 0);
    const first = buckets[0]?.count ?? 0;
    const last = buckets[buckets.length - 1]?.count ?? 0;
    const trendPercentage = first > 0 ? ((last - first) / first) * 100 : null;

    return {
        buckets: buckets.map((bucket) => ({
            period: String(bucket.period),
            total: bucket.count,
            by_type: {},
            by_camera: {},
        })),
        trend_direction: last > first ? "increasing" : last < first ? "decreasing" : "stable",
        trend_percentage: trendPercentage,
        total_alerts: totalAlerts,
        date_from: startDate,
        date_to: endDate,
    };
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
                time_interval: groupBy === "day" ? "DAILY" : groupBy === "week" ? "MONTHLY" : "YEARLY",
                time_period: toTimePeriod(startDate, endDate)

            });


            if (incidentType) params.set("incident_type", incidentType);
            if (cameraId) params.set("camera_id", cameraId);


            const result = await apiCall<AlertFrequencyMetricsRes>(`/alerts/alert-frequency-metrics?${params}`);
            setData(mapFrequencyResponse(result.data ?? [], startDate, endDate));
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
