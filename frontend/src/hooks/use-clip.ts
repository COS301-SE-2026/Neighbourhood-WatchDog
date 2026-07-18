import { useState, useCallback, useEffect, useRef } from "react";
import { apiFetch, ApiError } from "@/lib/api/alert";


export type ClipStatus = "idle" | "loading" | "ready" | "unavailable" | "expired" | "forbidden" | "error" | "processing";


interface ClipState {
    url: string | null;
    status: ClipStatus;
    errorMessage: string | null;

}


interface UseClipResult extends ClipState {
    loadClip: () => void;

}


const RETRY_DELAY = 5000;
const MAX_RETRY_ATTEMPTS = 10;

export function useClip(detectionEventId: string | null): UseClipResult {
    const [state, setState] = useState<ClipState>({
        url: null,
        status: "idle",
        errorMessage: null,
            
    });

            
    const attemptsRef = useRef(0);

    const loadClip = useCallback(async () => {
        if (!detectionEventId) return;

        setState((previous) => ({
            url: previous.url,
            status: attemptsRef.current === 0 ? "loading" : "processing",
            errorMessage: null
        }));

       


        try {
            const data = await apiFetch<{
                url: string,
                expires_in: number
            }>
            (`/api/clips/${detectionEventId}`);

            attemptsRef.current = 0;
            
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



     //running as soon as the new detection event appears
     useEffect(() => {

        if (!detectionEventId) {
            return;
        }

        attemptsRef.current = 0;
        let timeoutId: ReturnType<typeof setTimeout> | undefined;
        let cancelled = false;


        const pollForClip = async () => {
            if (cancelled) {
                return;
            }


            await loadClip();


            if (attemptsRef.current < MAX_RETRY_ATTEMPTS) {
                attemptsRef.current +=1;

                timeoutId = setTimeout(() => {
                    void pollForClip();

                }, RETRY_DELAY);
            }
            else {
                setState((previous) => 

                    previous.status === "processing" ? 
                    {
                        url: null,
                        status: "unavailable",
                        errorMessage: "Footage cannot be made available after processing."
                    } : previous
                );
            }
        };


        void pollForClip();


        return () => {
            cancelled = true;

            if (timeoutId) {
                clearTimeout(timeoutId);
            }
        };

     }, [detectionEventId, loadClip]);


    return { ...state, loadClip };

}