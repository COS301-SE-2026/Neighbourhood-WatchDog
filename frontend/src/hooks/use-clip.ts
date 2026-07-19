import { useState, useCallback, useEffect } from "react";
import { apiFetch, ApiError } from "@/lib/api/alert";


export type ClipStatus = "idle" | "loading" | "ready" | "unavailable" | "expired" | "forbidden" | "error" | "processing";


interface ClipState {
    url: string | null;
    status: ClipStatus;
    errorMessage: string | null;

}


interface UseClipResult extends ClipState {
    loadClip: () => Promise<void>;

}


type ClipRequestResult = "ready" | "retry" | "stop";

const RETRY_DELAY = 5000;
const MAX_RETRY_ATTEMPTS = 10;

export function useClip(detectionEventId: string | null): UseClipResult {
    const [state, setState] = useState<ClipState>({
        url: null,
        status: "idle",
        errorMessage: null,
            
    });


    const requestClip = useCallback(async (): Promise<ClipRequestResult> => {
        if (!detectionEventId){
            return "stop";
        }

        setState((previous) => ({
            ...previous,
            status: previous.status === "processing" ? "processing" : "loading",
            errorMessage: null
        }));


        
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

            return "ready";
        }
        catch (err: unknown) {
            
            if (typeof err === "object" && err !== null && "statusCode" in err) {
                const apiErr = err as ApiError;
            

                if (apiErr.statusCode === 410) {
                    setState({
                        url: null,
                        status: "expired",
                        errorMessage: "The clip has expired"
                    });

                    return "stop";
                }

                if (apiErr.statusCode === 403) {
                    setState({
                        url: null,
                        status: "forbidden",
                        errorMessage: "You do not have permission to view this footage"
                    });

                    return "stop";
                }

                if (apiErr.statusCode === 404) {
                    setState({
                        url: null,
                        status: "processing",
                        errorMessage: "Footage is being prepared..."
                    });

                    return "retry";
                }

                if (apiErr.statusCode === 503) {
                    setState({
                        url: null,
                        status: "unavailable",
                        errorMessage: "Clip storage is unavailable."
                    });

                    return "stop";
                }

            }

            setState({
                url: null,
                status: "error",
                errorMessage: "Failed to load footage"
            });

            return "stop";
                
            }
        
    }, [detectionEventId]);
    


        const loadClip = useCallback(async () => {
            await requestClip();
        }, [requestClip]);



     //running as soon as the new detection event appears
     useEffect(() => {

        if (!detectionEventId) {
            return;
        }

        let attempts = 0;
        let timeoutId: ReturnType<typeof setTimeout> | undefined;
        let cancelled = false;

        const poll = async () => {
            const result = await requestClip();

            if (cancelled || result !== "retry") {
                return;
            }


            attempts +=1;


            if (attempts >= MAX_RETRY_ATTEMPTS){
                setState({
                    url: null,
                    status: "unavailable",
                    errorMessage: "Footage was not available after processing."
                });

                return;
            }

            timeoutId = setTimeout(() => {
                void poll();
            }, RETRY_DELAY);

        };

       


        void poll();


        return () => {
            cancelled = true;

            if (timeoutId) {
                clearTimeout(timeoutId);
            }
        };

     }, [detectionEventId, requestClip]);


    return { ...state, loadClip };

}