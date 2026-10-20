"use client"

import { getAccessToken, refreshSession } from "@/lib/auth/cognito";
import { useEffect, useState, useRef } from "react";

export interface Track {
    track_id: number | string;
    confidence: number;
    bbox: [number, number, number, number]; // (l, t, r, b)
    detection_type?: string;
}

export interface AnnotationData {
    event: string;
    camera_id: string;
    tracks?: Track[];
    timestamp?: string;
}

function getAnnotationWebSocketBaseUrl(): string{
    
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;

    if (!apiUrl){
        
        const protocol = globalThis.location.protocol === "https:" ? "wss" : "ws";
        
        return `${protocol}://${globalThis.location.host}`;
    }

    const url = new URL(apiUrl);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";

    return url.origin;
}


export function useCameraAnnotations(cameraId: string) {
    const [annotations, setAnnotations] =
        useState<AnnotationData | null>(null);

    const [connection, setConnection] = useState<{
        cameraId: string | null;
        connected: boolean;
    }>({
        cameraId: null,
        connected: false,
    });

    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        let cancelled = false;
        let ws: WebSocket | null = null;
        let clearTimer: ReturnType<typeof setTimeout> | undefined;

        const connect = async () => {
            let token: string | null = null;

            try {
                // Access token lives in memory and expires; refresh if it's gone.
                token = getAccessToken() ?? (await refreshSession());
            } catch {
                token = null;
            }

            // The component may have unmounted (or cameraId changed) while we awaited.
            if (cancelled || !token) return;

            const baseUrl = getAnnotationWebSocketBaseUrl();
            const socket = new WebSocket(
                `${baseUrl}/api/stream/cameras/${cameraId}/annotations/ws?token=${encodeURIComponent(token)}`,
            );
            ws = socket;
            wsRef.current = socket;

            socket.onopen = () => {
                setConnection({
                    cameraId,
                    connected: true,
                });
            };

            socket.onclose = () => {
                setConnection((previous) =>
                    previous.cameraId === cameraId
                        ? {
                              cameraId,
                              connected: false,
                          }
                        : previous,
                );
            };

            socket.onerror = () => {
                setConnection((previous) =>
                    previous.cameraId === cameraId
                        ? {
                              cameraId,
                              connected: false,
                          }
                        : previous,
                );
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data) as AnnotationData;

                if (data.event === "ping") {
                    return;
                }

                setAnnotations(data);

                if (clearTimer) {
                    clearTimeout(clearTimer);
                }

                clearTimer = setTimeout(() => {
                    setAnnotations(null);
                }, 2000);
            };
        };

        void connect();

        return () => {
            cancelled = true;

            if (clearTimer) {
                clearTimeout(clearTimer);
            }

            ws?.close();
        };
    }, [cameraId]);



    const currentAnnotations =
        annotations?.camera_id === cameraId ? annotations : null;

    const currentConnected =
        connection.cameraId === cameraId && connection.connected;

    return {
        annotations: currentAnnotations,
        connected: currentConnected,
    };
}
