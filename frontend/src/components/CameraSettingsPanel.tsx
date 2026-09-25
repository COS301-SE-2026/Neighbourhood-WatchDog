"use client";
import React, { useEffect, useState } from "react";
import { useCameraSettings } from "@/hooks/use-camera-settings";
import { ZoneEditor } from "./ZoneEditor";
import { Button } from "./ui/button";
import { Slider } from "@/components/ui/slider";
import { LoaderCircle, Trash2, PlusCircle } from "lucide-react";
import {
    deleteCameraCoverage,
    getCameraCoverage,
    saveCameraCoverage,
} from "@/lib/api/camera";
import type { CameraCoverageInput } from "@/lib/validators/camera-coverage";
import { CameraCoverageEditor } from "./CameraCoverageEditor";


interface CameraSettingsPanelProps {
    readonly cameraId: string;
    readonly userRole: string;
    readonly videoRef: React.RefObject<HTMLVideoElement | null>;
    readonly propertyLatitude: number | null;
    readonly propertyLongitude: number | null;
}


//the roles that can access the zone settigns
const ADMIN_ROLES = new Set(["NEIGHBOURHOOD_ADMIN", "PROPERTY_ADMIN", "SYSTEM_ADMIN"])


export function CameraSettingsPanel({
    cameraId,
    userRole,
    videoRef,
    propertyLatitude,
    propertyLongitude,
}: CameraSettingsPanelProps) {
    const { settings, loading, updateThreshold, createZone, deleteZone, zoneMutation } = useCameraSettings(cameraId);

    const [drawingZone, setDrawingZone] = useState(false);
    const [threshold, setThreshold] = useState<number | null>(null);
    const [coverage, setCoverage] = useState<
        CameraCoverageInput | undefined
    >();
    const [coverageLoading, setCoverageLoading] = useState(true);
    const [coverageSaving, setCoverageSaving] = useState(false);
    const [coverageMessage, setCoverageMessage] = useState<string | null>(null);
    const [coverageError, setCoverageError] = useState<string | null>(null);

    useEffect(() => {
        if (!ADMIN_ROLES.has(userRole)) {
            return;
        }

        let cancelled = false;

        setCoverageLoading(true);
        setCoverageMessage(null);
        setCoverageError(null);

        void getCameraCoverage(cameraId)
            .then((savedCoverage) => {
                if (cancelled) {
                    return;
                }

                setCoverage(savedCoverage ?? undefined);
            })
            .catch((error) => {
                if (cancelled) {
                    return;
                }

                console.error("Failed to load camera POV", error);
                setCoverageError("Failed to load camera POV.");
            })
            .finally(() => {
                if (!cancelled) {
                    setCoverageLoading(false);
                }
            });

        return () => {
            cancelled = true;
        };
    }, [cameraId, userRole]);

    // resident role cannot see the panel
    if (!ADMIN_ROLES.has(userRole)) return null;

    if (loading) {

        return <p className="text-xs text-brand-ash">
            Loading settings...
        </p>

    }

    if(!settings) return null;


    const currentThreshold = threshold ?? settings.confidence_threshold;
    const applyingZone = zoneMutation !== null;
    const zoneStatusMessage = zoneMutation === "adding" ? "Applying new zone configuration…" : "Applying zone removal…";

    const handleThresholdCommit = async (val: number[]) => {
        await updateThreshold(val[0]);

    };

    const handleCoverageChange = (
        nextCoverage: CameraCoverageInput | undefined,
    ) => {
        setCoverage(nextCoverage);
        setCoverageMessage(null);
        setCoverageError(null);
    };

    const handleCoverageSave = async () => {
        if (!coverage) {
            setCoverageError(
                "Complete the camera POV before saving it.",
            );
            return;
        }

        setCoverageSaving(true);
        setCoverageMessage(null);
        setCoverageError(null);

        try {
            const savedCoverage = await saveCameraCoverage(
                cameraId,
                coverage,
            );

            setCoverage(savedCoverage);
            setCoverageMessage("Camera POV saved successfully.");
        } catch (error) {
            console.error("Failed to save camera POV", error);
            setCoverageError("Failed to save camera POV.");
        } finally {
            setCoverageSaving(false);
        }
    };

    const handleCoverageDelete = async () => {
        setCoverageSaving(true);
        setCoverageMessage(null);
        setCoverageError(null);

        try {
            await deleteCameraCoverage(cameraId);
            setCoverage(undefined);
            setCoverageMessage("Camera POV removed.");
        } catch (error) {
            console.error("Failed to remove camera POV", error);
            setCoverageError("Failed to remove camera POV.");
        } finally {
            setCoverageSaving(false);
        }
    };


    return (
        <div className="space-y-5 rounded-lg border border-border p-4">
            <h3 className="text-sm font-semibold text-brand-frost">
                Camera Detection Settings
            </h3>

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

                <p className="mt-1 text-xs text-brand-ash">
                    Detection below this confidence will not trigger alerts.
                </p>
            </div>

            <div>
                <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-medium text-brand-frost">
                        Detection zones
                    </span>

                    {!drawingZone && (
                        <Button
                            size="sm"
                            variant="outline"
                            disabled={applyingZone}
                            onClick={() => setDrawingZone(true)}
                            className="border-border bg-transparent text-brand-frost hover:bg-brand-slate hover:text-brand-frost"
                        >
                            <PlusCircle className="mr-1 h-3 w-3" />
                            Add zone
                        </Button>
                    )}
                </div>

                {applyingZone && (
                    <div
                        role="status"
                        aria-live="polite"
                        className="mb-3 flex items-center gap-2 rounded-md border border-brand-caution/30 bg-brand-slate px-3 py-2 text-xs text-brand-frost"
                    >
                        <LoaderCircle className="h-4 w-4 shrink-0 animate-spin text-brand-caution" />
                        <span>
                            {zoneStatusMessage} The live stream will update in a few seconds.
                        </span>
                    </div>
                )}

                {settings.zones.length === 0 && !drawingZone && (
                    <p className="text-xs text-brand-ash">
                        No zones configured. All detections trigger alerts.
                    </p>
                )}

                <ul className="space-y-1">
                    {settings.zones.map(zone => (
                        <li
                            key={zone.id}
                            className="flex items-center justify-between rounded bg-brand-slate px-2 py-1 text-xs text-brand-ash"
                        >
                            <span>{zone.name} ({zone.polygon.length} pts)</span>

                            <Button
                                size="icon"
                                variant="ghost"
                                disabled={applyingZone}
                                className="h-5 w-5 hover:bg-brand-slate"
                                aria-label={`Remove ${zone.name}`}
                                onClick={() => void deleteZone(zone.id)}
                            >
                                <Trash2 className="h-3 w-3 text-brand-threat" />
                            </Button>
                        </li>
                    ))}
                </ul>

                {drawingZone && (
                    <div className="mt-3">
                        <ZoneEditor
                            videoRef={videoRef}
                            onSave={async (polygon, name) => {
                                await createZone(polygon, name);
                                setDrawingZone(false);
                            }}
                            onCancel={() => setDrawingZone(false)}
                        />
                    </div>
                )}
            </div>

            <div className="space-y-3 border-t border-border pt-4">
                <div>
                    <h3 className="text-sm font-semibold text-brand-frost">
                        Geographic camera POV
                    </h3>

                    <p className="mt-1 text-xs text-brand-ash">
                        Choose the camera position within 100 metres of the
                        property, then select the left and right viewing edges.
                    </p>
                </div>

                {coverageLoading && (
                    <div
                        role="status"
                        className="flex items-center gap-2 text-xs text-brand-ash"
                    >
                        <LoaderCircle className="h-4 w-4 animate-spin" />
                        Loading camera POV…
                    </div>
                )}

                {!coverageLoading && (
                    <>
                        <CameraCoverageEditor
                            propertyLatitude={propertyLatitude}
                            propertyLongitude={propertyLongitude}
                            value={coverage}
                            onChange={handleCoverageChange}
                        />

                        <div className="flex flex-wrap gap-2">
                            <Button
                                type="button"
                                disabled={!coverage || coverageSaving}
                                onClick={() => void handleCoverageSave()}
                                className="bg-brand-green text-brand-void"
                            >
                                {coverageSaving
                                    ? "Saving POV…"
                                    : "Save camera POV"}
                            </Button>

                            <Button
                                type="button"
                                variant="outline"
                                disabled={!coverage || coverageSaving}
                                onClick={() => void handleCoverageDelete()}
                                className="border-border bg-transparent text-brand-frost"
                            >
                                Remove saved POV
                            </Button>
                        </div>
                    </>
                )}

                {coverageMessage && (
                    <p
                        role="status"
                        className="text-xs text-brand-green"
                    >
                        {coverageMessage}
                    </p>
                )}

                {coverageError && (
                    <p
                        role="alert"
                        className="text-xs text-brand-threat"
                    >
                        {coverageError}
                    </p>
                )}
            </div>

        </div>
    );
}