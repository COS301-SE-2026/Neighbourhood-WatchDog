"use client";
import React, { useState } from "react";
import { useAlertMetrics } from "@/hooks/use-alert-metrics";
import { Card } from "../ui/card";
import { RefreshCw } from "lucide-react";


interface AlertMetricsProps {
    readonly neighbourhoodId: string;
    readonly cameraOptions?: {
        id: string;
        name: string
    }[];
    readonly officerOptions?: {
        id: string;
        name: string
    }[];

}


function formatSeconds(seconds: number | null): string {

    if (seconds == null) return "-";
    if (seconds < 60) return `${Math.round(seconds)}s`;

    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);

    return `${mins}m ${secs}s`;

}


function StatusBadge({ status }: { status: string}) {

    const colours: Record<string, string> = {
        PENDING: "bg-yellow-500/20 text-yellow-400",
        ACKNOWLEDGED: "bg-green-500/20 text-green-400",
        RESOLVED: "bg-blue-500/20 text-blue-400"
 
    };
    
    return (
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${colours[status] ?? "bg-gray-500/20 text-gray-400"}`}>
            {status}
        </span>

    );

}

export function AlertMetrics({ neighbourhoodId, cameraOptions = [], officerOptions = []}: AlertMetricsProps) {

    const [cameraId, setCameraId] = useState<string | undefined>();
    const [officerId, setOfficerId] = useState<string | undefined>();

    const {metrics, loading, error, refetch } = useAlertMetrics(neighbourhoodId, cameraId, officerId);


    return (
        
        <div className="space-y-4">
            {/* summary cards */}
            <div className="grid grid-cols-3 gap-3">
                <Card className="p-4 bg-[#1S2A53] border-[#2D3A6E]">
                    <p className="text-xs text-slate-400 mb-1">Average Response Time</p>
                    <p className="text-2x1 font-bold text-white">
                        {loading ? "-" : formatSeconds(metrics?.average_response_seconds ??null)}

                    </p>
                </Card>
                <Card className="p-4 bg-[#1D2A5E] border-[#2D3A6E]">
                    <p className="text-xs text-slate-400 mb-1">Pending</p>
                    <p className="text-2xl font-bold text-yellow-400">
                        {loading ? "—" : (metrics?.pending_count ?? 0)}

                    </p>
                </Card>
                <Card className="p-4 bg-[#1D2A5E] border-[#2D3A6E]">
                    <p className="text-xs text-slate-400 mb-1">Acknowledged</p>
                    <p className="text-2xl font-bold text-green-400">
                        {loading ? "—" : (metrics?.acknowledged_count ?? 0)}

                    </p>
                </Card>
            </div>

             {/* filters */}
            <div className="flex gap-3 items-center">
                {cameraOptions.length > 0 && (
                    <select
                        value={cameraId ?? ""}
                        onChange={(e) => setCameraId(e.target.value || undefined)}
                        className="bg-[#1D2A5E] border border-[#2D3A6E] text-white text-xs rounded px-2 py-1"
                    >
                        <option value="">All cameras</option>
                        {cameraOptions.map((c) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>
                )}
                {officerOptions.length > 0 && (
                    <select
                        value={officerId ?? ""}
                        onChange={(e) => setOfficerId(e.target.value || undefined)}
                        className="bg-[#1D2A5E] border border-[#2D3A6E] text-white text-xs rounded px-2 py-1"
                    >
                        <option value="">All officers</option>
                        {officerOptions.map((o) => (
                            <option key={o.id} value={o.id}>{o.name}</option>
                        ))}
                    </select>
                )}
                <button
                    onClick={() => void refetch()}
                    disabled={loading}
                    className="ml-auto text-slate-400 hover:text-white transition-colors"
                    aria-label="Refresh metrics"
                >
                    <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                </button>
            </div>

             {/* per alert table */}
            {error ? (
                <p className="text-xs text-red-400">{error}</p>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-xs text-slate-300">
                        <thead>
                            <tr className="text-slate-500 border-b border-[#2D3A6E]">
                                <th className="text-left py-2 pr-4">Camera</th>
                                <th className="text-left py-2 pr-4">Created</th>
                                <th className="text-left py-2 pr-4">Status</th>
                                <th className="text-left py-2">Response Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={4} className="py-6 text-center text-slate-500">Loading…</td>
                                </tr>
                            ) : (metrics?.items ?? []).length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="py-6 text-center text-slate-500">No alerts</td>
                                </tr>
                            ) : (
                                (metrics?.items ?? []).map((item) => (
                                    <tr key={item.alert_id} className="border-b border-[#2D3A6E]/50">
                                        <td className="py-2 pr-4 font-mono text-[10px] truncate max-w-[120px]">
                                            {item.camera_id.slice(0, 8)}…
                                        </td>
                                        <td className="py-2 pr-4">
                                            {new Date(item.created_at).toLocaleString()}
                                        </td>
                                        <td className="py-2 pr-4">
                                            <StatusBadge status={item.status} />
                                        </td>
                                        <td className="py-2">
                                            {formatSeconds(item.response_seconds)}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
    

}