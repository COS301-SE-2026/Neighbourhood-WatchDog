"use client"
import CameraCard from "@/components/CameraCard"

import { useAlerts } from "@/hooks/use-alerts"
import { toast } from "sonner"
import { useEffect } from "react"


import { NewCameraCard } from "@/components/new-camera-card"
import { useState } from "react"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Camera {
    id: string;
    name: string;
    rtspUrl?: string;
}

const initialCameras: Camera[] = [
    { id: "1", name: "Camera 1 - Backyard" },
    { id: "2", name: "Camera 2 - Office Room 1", rtspUrl: "rtsp://Intrepid:password1234@172.20.10.2:554/stream2" },
    { id: "3", name: "Camera 5 - Living Room" },
    { id: "4", name: "Camera 3 - Bedroom 2" },
    { id: "5", name: "Camera 4 - Kitchen" },
]

export default function Dashboard() {

    const { alerts, connected } = useAlerts("10000000-0000-0000-0000-000000000001");

    useEffect(() => {
        if (alerts.length === 0) return;
        const latest = alerts[0];
        toast.warning("Human Detected", {
            description: `Camera ${latest.camera_id} - Confidence: ${(latest.confidence! * 100).toFixed(0)}%`,
        });
    }, [alerts]);

    const [showCard, setShowCard] = useState(false);
    const [cameras, setCameras] = useState<Camera[]>(initialCameras);

    const handleAcknowledge = (data: { cameraLocation: string; rtspUrl: string }) => {
        const newCamera: Camera = {
            id: crypto.randomUUID(),
            name: data.cameraLocation,
            rtspUrl: data.rtspUrl || undefined,
        };
        setCameras((prev) => [...prev, newCamera]);
        setShowCard(false);
    };

    return (
        <div className="w-full p-6">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Property Name</h1>
                <Button
                    onClick={() => setShowCard(true)}
                    className="bg-blue-500 hover:bg-blue-600 text-white rounded-full"
                >
                    <Plus size={16} className="mr-1" />
                    Add Camera
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cameras.map((camera) => (
                    <CameraCard
                        key={camera.id}
                        name={camera.name}
                        rtspUrl={camera.rtspUrl}
                    />
                ))}
            </div>

            {showCard && (
                <NewCameraCard
                    onClose={() => setShowCard(false)}
                    onAcknowledge={handleAcknowledge}
                />
            )}
        </div>
    )
}