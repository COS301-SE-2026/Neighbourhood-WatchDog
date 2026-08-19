"use client"
import { useRef, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { CameraOff, LoaderCircle, Radio, Video } from "lucide-react"
import CameraFeed, { type CameraStreamState } from "./CameraFeed"
import { CameraSettingsPanel } from "./CameraSettingsPanel"
import CameraDropdown from "./camera-dropdown"

interface CameraCardProps {
    readonly id: string;
    readonly name: string;
    readonly location: string;
    readonly visibility: "PUBLIC" | "PRIVATE" | "NEIGHBOURHOOD";
    readonly enabled: boolean;
    readonly userRole?: string;
}

function getStatusLabel(enabled: boolean, streamState: CameraStreamState): string {
    if (!enabled) return "Disabled";

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

function getStatusDotClass(enabled: boolean, streamState: CameraStreamState): string {
    if (!enabled) return "bg-amber-400";
    if (streamState === "unavailable") return "bg-red-400";
    if (streamState === "connecting") return "bg-white/40 animate-pulse";
    return "bg-emerald-400";
}

export default function CameraCard({ id, name, location, visibility, enabled, userRole = "RESIDENT" }: CameraCardProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [open, setOpen] = useState(false);
    const [streamState, setStreamState] = useState<CameraStreamState>("idle");
    const statusLabel = getStatusLabel(enabled, streamState);
    const statusDotClass = getStatusDotClass(enabled, streamState);
    const streamPath = `cameras/${id}`;

    function handleOpenChange(nextOpen: boolean) {
        setOpen(nextOpen);
        if (!nextOpen) setStreamState("idle");
    }

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <article className="overflow-hidden rounded-lg border border-white/10 bg-[#101011] transition-colors hover:border-white/20">
                <button
                    type="button"
                    onClick={() => setOpen(true)}
                    aria-label={`Open live stream for ${name}`}
                    className="relative flex aspect-video w-full flex-col items-center justify-center gap-2 bg-[#18181a] text-white/25 transition-colors hover:bg-[#1c1c1e]"
                >
                    <span className="absolute left-3 top-3 flex items-center gap-2 text-xs font-medium text-white/75">
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

                <div className="border-t border-white/10 p-4">
                    <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                            <h3 className="truncate text-sm font-semibold text-white">{name}</h3>
                            <p className="mt-1 truncate text-xs text-white/45">{location}</p>
                        </div>

                        <CameraDropdown
                            camera_id={id}
                            camera_name={name}
                            camera_location={location}
                            camera_visibility={visibility}
                            camera_enabled={enabled}
                        />
                    </div>

                    <div className="mt-4 border-t border-white/10 pt-3">
                        <p className="text-xs text-white/45">
                            Visibility: <span className="text-white/65">{visibility}</span>
                        </p>
                    </div>
                </div>
            </article>

            <DialogContent className="max-h-[90vh] w-full max-w-4xl overflow-y-auto border border-white/10 bg-[#0b0b0c] text-white">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-white">
                        {name}
                        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-white/70">
                            <span className={`size-1.5 rounded-full ${statusDotClass}`} />
                            {statusLabel}
                        </span>
                    </DialogTitle>
                </DialogHeader>

                {!enabled && (
                    <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md bg-[#18181a] text-white/45">
                        <CameraOff className="h-10 w-10" />
                        <p className="text-sm">This camera is currently disabled.</p>
                    </div>
                )}

                {enabled && streamState === "connecting" && (
                    <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md bg-[#18181a] text-white/45">
                        <LoaderCircle className="h-8 w-8 animate-spin" />
                        <p className="text-sm">Connecting to live stream…</p>
                    </div>
                )}

                {enabled && streamState === "unavailable" && (
                    <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md bg-[#18181a] text-white/45">
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
                    <div className="flex items-center gap-2 text-xs text-white/45">
                        <Radio className="h-3 w-3 text-emerald-400" />
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
