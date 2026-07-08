"use client";

import { useRef } from "react";
import { Film, Loader2, Ban, Lock, VideoOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useClip  } from "@/hooks/use-clip";


interface AlertFootagePlayerProps {
    readonly detectionEventId: string;
    readonly timestamp: string;

}

/**
 * 
 * inline video player for detection events
 * renders a 'view footage' button unitl clicked, then loads the clip
 *
 */

export function AlertFootagePlayer({ detectionEventId, timestamp }: AlertFootagePlayerProps) {
    const videoRef = useRef<HTMLVideoElement>(null);

    const { url, status, errorMessage, loadClip } = useClip(detectionEventId);

    const formattedTs = (() => {
        try {
            return new Intl.DateTimeFormat("en-ZA", {
                dateStyle: "medium", 
                timeStyle: "medium",

            }).format(new Date(timestamp));
        }
        catch {
            return timestamp;

        }
    })();



    //idle: trigger button
    if (status === "idle") {
        return (
            <Button
                variant="outline"
                size="sm"
                className="w-full border-sky/40 text-sky hover:bg-sky/10 hover:text-white font-mono text-xs gap-2"
                onClick={loadClip}
                aria-label="View footage for this alert"

            >
                <Film className="h-3.5 w-3.5" />
                View Footage
            </Button>
        );
    }


    //loading
    if (status === "loading") {
        return (
            <div className="flex items-center gap-2 text-xs text-mist/70 font-mono py-2">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-sky" />
                Loading clip…
            </div>
        );
    }


    //expired
    if (status === "expired") {
        return (
            <div className="flex items-center gap-2 text-xs text-mist/50 font-mono py-2 line-through">
                <VideoOff className="h-3.5 w-3.5 shrink-0" />
                {errorMessage ?? "Clip expired — retention period passed"}
            </div>
        );
    }

    //forbidden
     if (status === "forbidden") {
        return (
            <div className="flex items-center gap-2 text-xs text-caution/80 font-mono py-2">
                <Lock className="h-3.5 w-3.5 shrink-0" />
                {errorMessage ?? "You do not have permission to view this footage"}
            </div>
        );
    }

    //unavailable / error
    if (status === "unavailable" || status === "error") {
        return (
            <div className="flex items-center gap-2 text-xs text-mist/50 font-mono py-2">
                <Ban className="h-3.5 w-3.5 shrink-0" />
                {errorMessage ?? "Footage unavailable"}
            </div>
        );
    }


    //ready = inline player
    return (
        <div className="rounded-lg overflow-hidden border border-steel">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-black/40 border-b border-steel">
                <Film className="h-3 w-3 text-sky shrink-0" />
                <span className="text-xs font-mono text-mist/70 truncate">
                    {formattedTs}
                </span>
            </div>

            <video
                ref={videoRef}
                src={url!}
                controls
                autoPlay
                playsInline
                className="w-full max-h-56 bg-black"
                aria-label={`Detection footage at ${formattedTs}`}
            />

        </div>
    );

}