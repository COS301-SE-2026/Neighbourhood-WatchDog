"use client";
import React, { useState } from "react";
import { useCameraSettings } from "@/hooks/use-camera-settings";
import { ZoneEditor } from "./ZoneEditor";
import { Button } from "./ui/button";
import { Slider } from "@/components/ui/slider";
import { Trash2, PlusCircle } from "lucide-react";


interface CameraSettingsPanelProps {

    readonly cameraId: string;
    readonly userRole: string;
    readonly videoRef: React.RefObject<HTMLVideoElement | null>;

}


//the roles that can access the zone settigns
const ADMIN_ROLES = new Set(["NEIGHBOURHOOD_ADMIN", "PROPERTY_ADMIN", "SYSTEM_ADMIN"])


export function CameraSettingsPanel({
    cameraId,
    userRole, 
    videoRef
}: CameraSettingsPanelProps) {
    const { settings, loading, updateThreshold, createZone, deleteZone } = useCameraSettings(cameraId);

    const [drawingZone, setDrawingZone] = useState(false);
    const [threshold, setThreshold] = useState<number | null>(null);

    // resident role cannot see the panel
    if (!ADMIN_ROLES.has(userRole)) return null;

    if (loading) {

        return <p className="text-xs text-brand-ash">
            Loading settings...
        </p>

    }

    if(!settings) return null;


    const currentThreshold = threshold ?? settings.confidence_threshold;

    const handleThresholdCommit = async (val: number[]) => {
        await updateThreshold(val[0]);

    };


    return (
        <div className="space-y-5 p-4 border border-border rounded-lg">
            <h3 className="font-semibold text-sm text-brand-frost">Camera Detection Settings</h3>

            {/*confidence threshold*/}

            <div>
                <label className="text-xs text-brand-ash">
                    Confidence threshold: {Math.round(currentThreshold * 100)}%
                </label>

                <Slider
                    className="mt-2"
                    min={0}
                    max={1}
                    step={0.05}
                    value={[currentThreshold]}
                    onValueChange={val => setThreshold(val[0])}
                    onValueCommit={handleThresholdCommit}
                />
                
                <p className="text-xs text-brand-ash mt-1">
                    Detection below this confidence will not trigger alerts.
                </p>

            </div>


            {/*detection zones */}
            <div>
                <div className="flex items-center justify-between mb-2">

                <span className="text-xs font-medium text-brand-frost">Detection zones</span>

                {!drawingZone && (
                    <Button size="sm" variant="outline" onClick={() => setDrawingZone(true)} className="border-border bg-transparent text-brand-frost hover:bg-brand-slate hover:text-brand-frost">
                    <PlusCircle className="w-3 h-3 mr-1" /> Add zone
                    </Button>
                )}

                </div>

                {settings.zones.length === 0 && !drawingZone && (
                <p className="text-xs text-brand-ash">
                    No zones configured. All detections trigger alerts.
                </p>
                )}




                {/*existing zones list */}
                <ul className="space-y-1">
                {settings.zones.map(zone => (
                    <li key={zone.id} className="flex items-center justify-between text-xs bg-brand-slate text-brand-ash rounded px-2 py-1">

                    <span>{zone.name} ({zone.polygon.length} pts)</span>

                    <Button
                        size="icon"
                        variant="ghost"
                        className="h-5 w-5 hover:bg-brand-slate"
                        onClick={() => deleteZone(zone.id)}
                    >
                        <Trash2 className="w-3 h-3 text-brand-threat" />

                    </Button>
                    </li>
                ))}

                </ul>


                {/*zone drawing canvas */}
                {drawingZone && (
                <div className="mt-3">

                    <ZoneEditor
                    videoRef={videoRef}
                    onSave={async (polygon, name) => {
                        await createZone(polygon, name)
                        setDrawingZone(false)
                    }}
                    onCancel={() => setDrawingZone(false)}
                    />
                    
                </div>
                )}
            </div>
        </div>
    )

}
