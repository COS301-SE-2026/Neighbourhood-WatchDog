"use client"

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
        const baseUrl = getAnnotationWebSocketBaseUrl();

        const ws = new WebSocket(
            `${baseUrl}/api/stream/cameras/${cameraId}/annotations/ws`,
        );

        let clearTimer: ReturnType<typeof setTimeout> | undefined;

        ws.onopen = () => {
            setConnection({
                cameraId,
                connected: true,
            });
        };

        ws.onclose = () => {
            setConnection((previous) =>
                previous.cameraId === cameraId
                    ? {
                          cameraId,
                          connected: false,
                      }
                    : previous,
            );
        };

        ws.onerror = () => {
            setConnection((previous) =>
                previous.cameraId === cameraId
                    ? {
                          cameraId,
                          connected: false,
                      }
                    : previous,
            );
        };

        ws.onmessage = (event) => {
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

        wsRef.current = ws;

        return () => {
            if (clearTimer) {
                clearTimeout(clearTimer);
            }

            ws.close();
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
