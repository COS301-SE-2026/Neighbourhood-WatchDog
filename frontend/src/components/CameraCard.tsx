"use client"
import { useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { CameraOff, LoaderCircle, Radio, Video } from "lucide-react"
import CameraFeed, {type CameraStreamState} from "./CameraFeed"
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


function getStatusLabel(enabled: boolean, streamState: CameraStreamState): string{
    if (!enabled) return "disabled";

    switch (streamState){
        case "connecting":
            return "connecting";
        case "live":
            return "live";
        case "unavailable":
            return "unavailable";
        
        default:
            return "ready";
    }
}


function getStatusVariant(enabled: boolean, streamState: CameraStreamState): "success" | "destructive" | "secondary"{
    if (!enabled || streamState === "unavailable") return "destructive";

    if (streamState === "live") return "success";

    return "secondary";
}




export default function CameraCard({ id, name, location, visibility, enabled, userRole = "RESIDENT" }: CameraCardProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [open, setOpen] = useState(false);
    const [streamState, setStreamState] = useState<CameraStreamState>("idle");
    const statusLabel = getStatusLabel(enabled, streamState);
    const statusVariant = getStatusVariant(enabled, streamState);
    const streamPath = `camera/${id}`;


    function handleOpenChange(nextOpen: boolean){
        setOpen(nextOpen);

        if (!nextOpen) setStreamState("idle");
    }

    

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
                <Card className="transition-all hover:ring-2 hover:ring-primary/50">
                    <CardHeader className="flex flex-row items-center justify-between p-4">
                        <CardTitle className="text-sm font-medium">{name}</CardTitle>

                        <div className="flex flex-row items-center gap-2">
                            <Badge variant={statusVariant}>{statusLabel}</Badge>

                            <CameraDropdown
                                camera_id={id}
                                camera_name={name}
                                camera_location={location}
                                camera_visibility={visibility}
                                camera_enabled={enabled}
                            />
                        </div>
                    </CardHeader>

                    <CardContent className="p-4 pt-0">
                        <button
                            type="button"
                            onClick={() => setOpen(true)}
                            className="flex spect-video w-full flex-col items-center justify-center gap-2 rounded-md bg-muted text-muted-foreground transition-colors hover:bg-muted/70"
                            aria-label={`Open live stream for ${name}`}
                            >
                                {enabled ? (
                                    <>
                                        <Video className="h-8 w-8" />
                                        <span className="text-sm">Select to play live stream</span>
                                    </>
                                ): (
                                    <>
                                        <CameraOff className="h-8 w-8" />
                                        <span className="text-sm">Camera is disabled</span>
                                    </>
                                )}
                            </button>
                    </CardContent>
                </Card>

                <DialogContent className="max-h-[90vh] w-full max-w-4xl overflow-y-auto">
                    <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        {name}
                        <Badge variant={statusVariant}>{statusLabel}</Badge>
                    </DialogTitle>
                    </DialogHeader>

                    {!enabled && (
                    <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md bg-muted text-muted-foreground">
                        <CameraOff className="h-10 w-10" />
                        <p className="text-sm">This camera is currently disabled.</p>
                    </div>
                    )}

                    {enabled && streamState === "connecting" && (
                    <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md bg-muted text-muted-foreground">
                        <LoaderCircle className="h-8 w-8 animate-spin" />
                        <p className="text-sm">Connecting to live stream…</p>
                    </div>
                    )}

                    {enabled && streamState === "unavailable" && (
                    <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md bg-muted text-muted-foreground">
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

                    {enabled && open && streamState === "idle" && (
                    <div className="hidden">
                        <CameraFeed
                        ref={videoRef}
                        streamPath={streamPath}
                        cameraId={id}
                        onStreamStateChange={setStreamState}
                        />
                    </div>
                    )}

                    {enabled && streamState === "live" && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Radio className="h-3 w-3 text-green-500" />
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
