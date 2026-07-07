"use client";
import React, { useState } from "react";
import { Card } from "../ui/card";
import { RefreshCw } from "lucide-react";
import { useAlertTrends } from "@/hooks/use-alert-trends";
import { IncidentTrendChart } from "./IncidentTrendChart"; //needs to be completed by OEM
import { setgroups } from "process";


const DETECTION_TYPES = [
    "HUMAN_PRESENCE",
    "WEAPON_DETECTION",
    "LOITERING",
    "PERIMETER_SCAN",
    "FALL_DETECTED"

];

interface IncidentTrendProps{
    readonly neighbourhoodId: string;

}


function toISODate(d: Date) {
    return d.toISOString().split("T")[0];

}


export function IncidentTrends({ neighbourhoodId }: IncidentTrendProps) {

    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);


    const [startDate, setStartDate] = useState(toISODate(thirtyDaysAgo));
    const [endDate, setEndDate] = useState(toISODate(today));
    const [groupBy, setGroupBy] = useState<"day" | "week" | "month">("day");
    const [incidentType, setIncidentType] = useState<string | undefined>();


    const { data, loading, error, refetch } = useAlertTrends(neighbourhoodId, startDate, endDate, groupBy, incidentType);


    return(

        <div className="space-y-4">
            {/*filter controls*/}
            <div className="flex flex-wrap gap-3 items-center">
                <div className="flex items-center gap-1">
                    <label className="text-xs text-slate-400">From</label>
                    <input type="date" value={startDate}
                            onChange={e => setStartDate(e.target.value)}
                            className="bg-[#1D2A5E] border border-[#2D3A6E] text-white text-xs rounded px-2 py-1" />
                </div>

                <div className="flex items-center gap-1">
                    <label className="text-xs text-slate-400">To</label>
                    <input type="date" value={endDate}
                            onChange={e => setEndDate(e.target.value)}
                            className="bg-[#1D2A5E] border border-[#2D3A6E] text-white text-xs rounded px-2 py-1" />
                </div>

                <select value={groupBy}
                        onChange={e => setGroupBy(e.target.value as "day" | "week" | "month")}
                        className="bg-[#1D2A5E] border border-[#2D3A6E] text-white text-xs rounded px-2 py-1">

                    <option value="day">By day</option>
                    <option value="week">By week</option>
                    <option value="month">By month</option>
                </select>

                <select value={incidentType ?? ""}
                        onChange={e => setIncidentType(e.target.value || undefined)}
                        className="bg-[#1D2A5E] border border-[#2D3A6E] text-white text-xs rounded px-2 py-1">

                    <option value="">All types</option>
                    {DETECTION_TYPES.map(t => <option key={t}>{t.replace("_", " ")}</option>)}
                </select>

                <button onClick={() => void refetch()} disabled={loading}
                        className="text-slate-400 hover:text-white ml-auto" aria-label="Refresh">

                    <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />

                </button>
            </div>



            {/*summaries*/}
            {data && (
                <div className="text-xs text-slate-400">
                    {data.total_alerts} incidents from {data.date_from} to {data.date_to}
                </div>
            )}


            {/*chart*/}
            {error ? (
                <p className="text-xs text-red-400">{error}</p>
            ): loading ? (
                <div className="flex justify-center py-8">
                    <RefreshCw className="h-5 w-5 animate-spin text-sky-400" />
                </div>

            ): data?.buckets.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-8">No incidents in this date range</p>

            ): data ? (
                <IncidentTrendChart
                    buckets={data.buckets}
                    trendDirection={data.trend_direction}
                    trendPercentage={data.trend_percentage}
                
                />

            ): null}
        </div>

    );
}