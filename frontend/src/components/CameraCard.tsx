"use client"
import { useRef, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { CameraOff, LoaderCircle, Radio, Video, TriangleAlert } from "lucide-react"
import CameraFeed, { type CameraStreamState } from "./CameraFeed"
import { CameraSettingsPanel } from "./CameraSettingsPanel"
import CameraDropdown from "./camera-dropdown"

interface CameraCardProps {
    readonly id: string;
    readonly name: string;
    readonly location: string;
    readonly visibility: "PUBLIC" | "PRIVATE" | "NEIGHBOURHOOD";
    readonly enabled: boolean;
    readonly edgeAgentAvailable?: boolean | null;
    readonly userRole?: string;
    readonly onDeleted: (cameraId: string) => void;
}

function getStatusLabel(enabled: boolean, streamState: CameraStreamState, edgeAgentAvailable?: boolean | null): string {
    if (!enabled) return "Disabled";

    if (edgeAgentAvailable === false) return "Degraded";


    switch (streamState) {
        case "connecting":
            return "Connecting";
        case "live":
            return "Live";
        case "unavailable":
            return "Unavailable";
        default:
            return "Enabled";
    }
}

function getStatusDotClass(enabled: boolean, streamState: CameraStreamState, edgeAgentAvailable?: boolean | null): string {
    if (!enabled) return "bg-brand-caution";
    if (edgeAgentAvailable === false) return "bg-brand-caution";
    if (streamState === "unavailable") return "bg-brand-threat";
    if (streamState === "connecting") return "bg-brand-ash/40 animate-pulse";
    return "bg-brand-green";
}

export default function CameraCard({ id, name, location, visibility, enabled, edgeAgentAvailable, userRole = "RESIDENT", onDeleted }: CameraCardProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [open, setOpen] = useState(false);
    const [streamState, setStreamState] = useState<CameraStreamState>("idle");
    const agentDegraded = enabled && edgeAgentAvailable === false;
    const statusLabel = getStatusLabel(enabled, streamState, edgeAgentAvailable);
    const statusDotClass = getStatusDotClass(enabled, streamState, edgeAgentAvailable);
    const streamPath = `cameras/${id}`;

    function handleOpenChange(nextOpen: boolean) {
        setOpen(nextOpen);
        if (!nextOpen) setStreamState("idle");
    }

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <article className="overflow-hidden rounded-lg border border-border bg-brand-depth text-brand-frost transition-colors hover:border-brand-gunmetal/30">
                <button
                    type="button"
                    onClick={() => setOpen(true)}
                    aria-label={`Open live stream for ${name}`}
                    className="relative flex aspect-video w-full flex-col items-center justify-center gap-2 bg-brand-slate text-brand-ash/25 transition-colors hover:bg-brand-abyss"
                >
                    <span className="absolute left-3 top-3 flex items-center gap-2 text-xs font-medium text-brand-ash/75">
                        <span className={`size-1.5 rounded-full ${statusDotClass}`} />
                        {statusLabel}
                    </span>

                    {enabled ? (
                        <>
                            <Video className="size-6" />
                            <span className="text-xs">Select to play live stream</span>
                        </>
                    ) : (
                        <>
                            <CameraOff className="size-6" />
                            <span className="text-xs">Camera is disabled</span>
                        </>
                    )}
                </button>

                <div className="border-t border-border p-4">
                    <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                            <h3 className="truncate text-sm font-semibold text-brand-ash">{name}</h3>
                            <p className="mt-1 truncate text-xs text-brand-ash/45">{location}</p>
                        </div>

                        <CameraDropdown
                            camera_id={id}
                            camera_name={name}
                            camera_location={location}
                            camera_visibility={visibility}
                            camera_enabled={enabled}
                            onDeleted={onDeleted}
                        />
                    </div>

                    <div className="mt-4 border-t border-border pt-3">
                        <p className="text-xs text-brand-ash/45">
                            Visibility: <span className="text-brand-ash/65">{visibility}</span>
                        </p>

                        {agentDegraded && (
                            <div
                                role="status"
                                className="mt-3 flex items-start gap-2 rounded-md border border-brand-caution/20 bg-brand-caution/10 px-3 py-2 text-xs text-brand-caution"
                            >
                                <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-brand-caution" />
                                <span>
                                    Stream quality degraded due to agent failure. The system is attempting to keep video available while the Agent reconnects.
                                </span>
                            </div>
                        )}

                    </div>
                </div>
            </article>

            <DialogContent className="max-h-[90vh] w-full max-w-4xl overflow-y-auto border text-brand-frost border-border text-brand-ash">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-brand-ash">
                        {name}
                        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-ash/70">
                            <span className={`size-1.5 rounded-full ${statusDotClass}`} />
                            {statusLabel}
                        </span>
                    </DialogTitle>
                </DialogHeader>

                {agentDegraded && (
                    <div
                        role="status"
                        className="flex items-start gap-2 rounded-md border border-brand-caution/20 bg-brand-caution/10 px-3 py-2 text-xs text-brand-caution"
                    >
                        <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-brand-caution" />
                        <span>
                            Stream quality degraded due to agent failure. The system is attempting to keep video available while the Agent reconnects.
                        </span>
                    </div>
                )}

                {!enabled && (
                    <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md bg-brand-slate text-brand-ash/45">
                        <CameraOff className="h-10 w-10" />
                        <p className="text-sm">This camera is currently disabled.</p>
                    </div>
                )}

                {enabled && streamState === "connecting" && (
                    <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md bg-brand-slate text-brand-ash/45">
                        <LoaderCircle className="h-8 w-8 animate-spin" />
                        <p className="text-sm">Connecting to live stream…</p>
                    </div>
                )}

                {enabled && streamState === "unavailable" && (
                    <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md bg-brand-slate text-brand-ash/45">
                        <CameraOff className="h-10 w-10" />
                        <p className="text-sm">Live stream is currently unavailable.</p>
                        <p className="text-xs">
                            Confirm that the camera is enabled and actively publishing.
                        </p>
                    </div>
                )}

                {enabled && open && streamState !== "unavailable" && (
                    <div className={streamState === "connecting" ? "hidden" : undefined}>
                        <CameraFeed
                            ref={videoRef}
                            streamPath={streamPath}
                            cameraId={id}
                            onStreamStateChange={setStreamState}
                        />
                    </div>
                )}

                {enabled && streamState === "live" && (
                    <div className="flex items-center gap-2 text-xs text-brand-ash/45">
                        <Radio className="h-3 w-3 text-brand-green" />
                        Live via MediaMTX WebRTC
                    </div>
                )}

                <CameraSettingsPanel
                    cameraId={id}
                    userRole={userRole}
                    videoRef={videoRef}
                />
            </DialogContent>
        </Dialog>
    )
}
