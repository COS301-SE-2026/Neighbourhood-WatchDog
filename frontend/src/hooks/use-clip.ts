import { useState, useCallback, useEffect } from "react";
import { apiFetch, ApiError } from "@/lib/api/alert";

export type ClipStatus = "idle"| "loading" | "ready"  | "unavailable" | "expired"  | "forbidden" | "error" | "processing";

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

const setGenericError = (
    setState: React.Dispatch<React.SetStateAction<ClipState>>,
): ClipRequestResult => {
    setState({
        url: null,
        status: "error",
        errorMessage: "Failed to load footage",
    });

    return "stop";
};

const handleApiError = (
    error: ApiError,
    setState: React.Dispatch<React.SetStateAction<ClipState>>,
): ClipRequestResult => {
    switch (error.statusCode) {
        case 410:
            setState({
                url: null,
                status: "expired",
                errorMessage: "The clip has expired",
            });
            return "stop";

        case 403:
            setState({
                url: null,
                status: "forbidden",
                errorMessage:
                    "You do not have permission to view this footage",
            });
            return "stop";

        case 404:
            setState({
                url: null,
                status: "processing",
                errorMessage: "Footage is being prepared...",
            });
            return "retry";

        case 503:
            setState({
                url: null,
                status: "unavailable",
                errorMessage: "Clip storage is unavailable.",
            });
            return "stop";

        default:
            return setGenericError(setState);
    }
};

export function useClip(
    detectionEventId: string | null,
): UseClipResult {
    const [state, setState] = useState<ClipState>({
        url: null,
        status: "idle",
        errorMessage: null,
    });

    const requestClip = useCallback(
        async (): Promise<ClipRequestResult> => {
            if (!detectionEventId) {
                return "stop";
            }

            setState((previous) => ({
                ...previous,
                status:
                    previous.status === "processing"
                        ? "processing"
                        : "loading",
                errorMessage: null,
            }));

            try {
                const data = await apiFetch<{
                    url: string;
                    expires_in: number;
                }>(`/api/clips/${detectionEventId}`);

                setState({
                    url: data.url,
                    status: "ready",
                    errorMessage: null,
                });

                return "ready";
            } catch (err: unknown) {
                if (
                    typeof err === "object" &&
                    err !== null &&
                    "statusCode" in err
                ) {
                    return handleApiError(
                        err as ApiError,
                        setState,
                    );
                }

                return setGenericError(setState);
            }
        },
        [detectionEventId],
    );

    const loadClip = useCallback(async () => {
        await requestClip();
    }, [requestClip]);

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

            attempts += 1;

            if (attempts >= MAX_RETRY_ATTEMPTS) {
                setState({
                    url: null,
                    status: "unavailable",
                    errorMessage:
                        "Footage was not available after processing.",
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