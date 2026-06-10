"use client"

import { useEffect, useState, useRef } from "react";

export interface Track {

    track_id: number;
    confidence: number;
    bbox: [number, number, number, number]; //(l, t, r, b)

}


export interface AnnotationData {

    event: string;
    camera_id: string;
    tracks?: Track[];
    timestamp?: string;

}


export function useCameraAnnotations(cameraId: string) {

    const [annotations, setAnnotations] = useState<AnnotationData | null>(null);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {

        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        const ws = new WebSocket(`${protocol}://localhost:8000/api/stream/cameras/${cameraId}/annotations/ws`);

        ws.onopen = () => setConnected(true);
        ws.onclose = () => setConnected(false);


        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("WS received:", data.event, "tracks:", data.tracks?.length ?? 0);
            if (data.event === "ping") return;
            setAnnotations(data);
        };

        wsRef.current = ws;
        return () => ws.close();

    }, [cameraId]);


    return { annotations, connected };


}