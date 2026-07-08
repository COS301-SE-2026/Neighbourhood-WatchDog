import { useState, useCallback } from "react";
import { apiFetch, ApiError } from "@/lib/api/alert";


export type ClipStatus = "idle" | "loading" | "ready" | "unavailable" | "expired" | "forbidden" | "error";


interface ClipState {
    url: string | null;
    status: ClipStatus;
    errorMessage: string | null;

}


interface UseClipResult extends ClipState {
    loadClip: () => void;

}


export function useClip(detectionEventId: string | null): UseClipResult {
    const [state, setState] = useState<ClipState>({
        url: null,
        status: "idle",
        errorMessage: null,
            
    });

    const loadClip = useCallback(async () => {
        if (!detectionEventId) return;

        setState({
            url: null,
            status: "loading",
            errorMessage: null
        });


        try {
            const data = await apiFetch<{
                url: string,
                expires_in: number
            }>
            (`/api/clips/${detectionEventId}`);
            
            setState({
                url: data.url,
                status: "ready",
                errorMessage: null
            });
        }
        catch (err: unknown) {
            
            if (typeof err === "object" && err !== null && "statusCode" in err) {
                const apiErr = err as ApiError;
            

                if (apiErr.statusCode === 410) {
                    setState({
                        url: null,
                        status: "expired",
                        errorMessage: "The clip has exired"
                    });
                }

                else if (apiErr.statusCode === 403) {
                    setState({
                        url: null,
                        status: "forbidden",
                        errorMessage: "You do not have permission to view this footage"
                    });
                }

                else if (apiErr.statusCode === 404) {
                    setState({
                        url: null,
                        status: "unavailable",
                        errorMessage: "No footage is available for this event"
                    });
                }

                else if (apiErr.statusCode === 503) {
                    setState({
                        url: null,
                        status: "unavailable",
                        errorMessage: "Clip storage is not configured"
                    });
                }

                else {
                    setState({
                        url: null,
                        status: "error",
                        errorMessage: "Failed to load footage"
                    });
                }
            }
            else {
                setState({
                    url: null,
                    status: "error",
                    errorMessage: "Failed to load footage"
                });
            }
        }
    }, [detectionEventId]);


    return { ...state, loadClip };

}