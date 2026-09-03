"use client";


import { Film, Loader2, Ban, Lock, VideoOff } from "lucide-react";
import { useClip  } from "@/hooks/use-clip";


interface AlertFootagePlayerProps {
    readonly alertId: string;
    readonly timestamp: string;

}

/**
 * 
 * inline video player for detection events
 * renders a 'view footage' button unitl clicked, then loads the clip
 *
 */

export function AlertFootagePlayer({ alertId, timestamp }: AlertFootagePlayerProps) {
    // const videoRef = useRef<HTMLVideoElement>(null);

    const { url, status, errorMessage, loadClip } = useClip(alertId);

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



    // //idle: trigger button
    // if (status === "idle") {
    //     return (
    //         <Button
    //             variant="outline"
    //             size="sm"
    //             className="w-full border-brand-pulse/40 text-brand-pulse hover:bg-sky/10 hover:text-brand-frost font-mono text-xs gap-2"
    //             onClick={loadClip}
    //             aria-label="View footage for this alert"

    //         >
    //             <Film className="h-3.5 w-3.5" />
    //             View Footage
    //         </Button>
    //     );
    // }


    // //loading
    // if (status === "loading") {
    //     return (
    //         <div className="flex items-center gap-2 text-xs text-mist/70 font-mono py-2">
    //             <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-pulse" />
    //             Loading clip…
    //         </div>
    //     );
    // }

    if (status === "idle" || status === "loading" || status === "processing") {
        return (
            <div className="flex items-center gap-2 py-2 text-xs font-mono text-mist/70">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-pulse" />
                {
                    status === "processing" ? "Footage is being prepared..." : "Loading footage..."
                }
            </div>
        );
    }


    //expired
    if (status === "expired") {
        return (
            <div className="flex items-center gap-2 py-2 text-xs font-mono text-mist/50 line-through">
                <VideoOff className="h-3.5 w-3.5 shrink-0" />
                {errorMessage ?? "Clip expired - retention period passed"}
            </div>
        );
    }

    //forbidden
     if (status === "forbidden") {
        return (
            <div className="flex items-center gap-2 py-2 text-xs font-mono text-caution/80">
                <Lock className="h-3.5 w-3.5 shrink-0" />
                {errorMessage}
            </div>
        );
    }

    //unavailable / error
    if (status === "unavailable" || status === "error") {
        return (
            <div className="flex items-center gap-2 py-2 text-xs font-mono text-mist/50">
                <Ban className="h-3.5 w-3.5 shrink-0" />
                {errorMessage ?? "Footage unavailable"}
            </div>
        );
    }


    //ready = inline player
    return (
        <div className="rounded-lg overflow-hidden border border-brand-gunmetal">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-brand-void/40 border-b border-brand-gunmetal">
                <Film className="h-3 w-3 text-brand-pulse shrink-0" />
                <span className="text-xs font-mono text-mist/70 truncate">
                    {formattedTs}
                </span>
            </div>

            <video
                key={url}
                src={url!}
                controls
                autoPlay
                muted
                playsInline
                className="w-full max-h-56 bg-brand-void"
                aria-label={`Detection footage at ${formattedTs}`}
            />

        </div>
    );

}