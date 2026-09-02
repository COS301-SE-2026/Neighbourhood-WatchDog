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

        return <p className="text-xs text-white/45">
            Loading settings...
        </p>

    }

    if(!settings) return null;


    const currentThreshold = threshold ?? settings.confidence_threshold;

    const handleThresholdCommit = async (val: number[]) => {
        await updateThreshold(val[0]);

    };


    return (
        <div className="space-y-5 p-4 border border-white/10 rounded-lg">
            <h3 className="font-semibold text-sm text-white">Camera Detection Settings</h3>

            {/*confidence threshold*/}

            <div>
                <label className="text-xs text-white/45">
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
                
                <p className="text-xs text-white/45 mt-1">
                    Detection below this confidence will not trigger alerts.
                </p>

            </div>


            {/*detection zones */}
            <div>
                <div className="flex items-center justify-between mb-2">

                <span className="text-xs font-medium text-white">Detection zones</span>

                {!drawingZone && (
                    <Button size="sm" variant="outline" onClick={() => setDrawingZone(true)} className="border-white/10 bg-transparent text-white/80 hover:bg-white/5 hover:text-white">
                    <PlusCircle className="w-3 h-3 mr-1" /> Add zone
                    </Button>
                )}

                </div>

                {settings.zones.length === 0 && !drawingZone && (
                <p className="text-xs text-white/45">
                    No zones configured. All detections trigger alerts.
                </p>
                )}




                {/*existing zones list */}
                <ul className="space-y-1">
                {settings.zones.map(zone => (
                    <li key={zone.id} className="flex items-center justify-between text-xs bg-white/5 text-white/70 rounded px-2 py-1">

                    <span>{zone.name} ({zone.polygon.length} pts)</span>

                    <Button
                        size="icon"
                        variant="ghost"
                        className="h-5 w-5 hover:bg-white/10"
                        onClick={() => deleteZone(zone.id)}
                    >
                        <Trash2 className="w-3 h-3 text-red-400" />

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
