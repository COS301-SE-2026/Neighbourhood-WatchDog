"use client"

import { clear } from "console";
import { useEffect, useState, useRef } from "react";
import { ur } from "zod/locales";

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
    const [annotations, setAnnotations] = useState<AnnotationData | null>(null);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const baseUrl = getAnnotationWebSocketBaseUrl();
        const ws = new WebSocket(`${baseUrl}://localhost:8000/api/stream/cameras/${cameraId}/annotations/ws`);


         //clearing canvas if no data comes for 2 seconds
        let clearTimer: ReturnType<typeof setTimeout>;

        ws.onopen = () => setConnected(true);
        ws.onclose = () => setConnected(false);

        ws.onerror = () => setConnected(false);


    

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data) as AnnotationData;
            if (data.event === "ping") return;
            setAnnotations(data);

            //clearing annotations 2 seconds after the last update
            if (clearTimer) clearTimeout(clearTimer);
            
            clearTimer = setTimeout(() => {
                setAnnotations(null);
            }, 2000);

        };

        wsRef.current = ws;
        return () => {
            if (clearTimer) clearTimeout(clearTimer);
            ws.close();
        }
    }, [cameraId]);

    return { annotations, connected };
}
