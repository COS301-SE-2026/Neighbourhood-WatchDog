"use client"
import CameraCard from "@/components/CameraCard"
import type { Camera } from "@/lib/validators/camera"
import { useAlerts } from "@/hooks/use-alerts"
import { toast } from "sonner"
import { useEffect, useState } from "react"

import { addCamera as apiAddCamera, fetchCameras as apiFetchCameras } from "@/lib/api/camera"
import { NewCameraCard } from "@/components/new-camera-card"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAppView } from "@/components/app-view-context"

interface CameraProp {
    id: string;
    name: string;
    visibility: Camera["visibility"],
    enabled: boolean
    location: string
    rtspUrl?: string;
}

const initialCameras: CameraProp[] = [
    { id: "1", name: "Camera 1 - Backyard" , visibility: "PRIVATE", enabled: true, location: "Backyard"},
  //{ id: "2", name: "Camera 2 - Office Room 1", rtspUrl: "rtsp://Intrepid:password1234@172.20.10.2:554/stream2" },
    { id: "40000000-0000-0000-0000-000000000001", name: "Camera 2 - Office Room 1", rtspUrl: "rtsp://localhost:8554/" + "cameras/40000000-0000-0000-0000-000000000001", visibility: "PRIVATE", enabled: true, location: "Office Room" },
    { id: "3", name: "Camera 5 - Living Room", visibility: "PRIVATE", enabled: true, location: "Living Room" },
    { id: "4", name: "Camera 3 - Bedroom 2", visibility: "PRIVATE", enabled: true, location: "Bedroom" },
    { id: "5", name: "Camera 4 - Kitchen", visibility: "PRIVATE",enabled: true, location: "Kitchen" },
]



export default function Dashboard() {
    const { propertyId } = useAppView()
    const { alerts, connected } = useAlerts("10000000-0000-0000-0000-000000000001");

    useEffect(() => {
        if (alerts.length === 0) return;
        const latest = alerts[0];
        toast.error("Human Detected", {
            description: `Camera ${latest.camera_id} - Confidence: ${(latest.confidence! * 100).toFixed(0)}%`,
        });
    }, [alerts]);

    const [showCard, setShowCard] = useState(false);
    const [cameras, setCameras] = useState<CameraProp[]>([]);

    useEffect(() => {
        if (!propertyId) return;

        apiFetchCameras(propertyId)
            .then((data) => {
                setCameras(
                    data.map((c) => ({
                        id: c.id,
                        name: c.name,
                        location: c.location,
                        visibility: c.visibility,
                        enabled: c.enabled,
                    }))
                );
            })
            .catch((err) => {
                console.error("Failed to fetch cameras", err);
                toast.error("Failed to load cameras");
            });
    }, [propertyId]);

    const handleAcknowledge = async (data: { name: string, location: string, rtspUrl: string }) => {
        if (!propertyId) {
            toast.error("Select a property before adding a camera");
            return;
        }
        const newCamera = await apiAddCamera({
            name: data.name,
            location: data.location,
            visibility: "PRIVATE",
            enabled: true,
            rtsp_url: data.rtspUrl,
            property_id: propertyId
        });
        setCameras((prev) => [...prev, 
            {
        id: newCamera.id,
        name: newCamera.name,
        location: newCamera.location,
        visibility: newCamera.visibility,
        enabled: newCamera.enabled,
            }
        ]);
        setShowCard(false);
    };

    return (
        <div className="w-full p-6">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Property Name</h1>
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="text-sm">{connected ? 'Connected' : 'Disconnected'}</span>
                    <Button
                        onClick={() => setShowCard(true)}
                        className="bg-blue hover:bg-sky text-white rounded-full"
                    >
                        <Plus size={16} className="mr-1" />
                        Add Camera
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cameras.map((camera) => (
                    <CameraCard
                        key={camera.id}
                        id={camera.id}
                        name={camera.name}
                        location={camera.location}
                        visibility={camera.visibility}
                        enabled={camera.enabled}
                        userRole="NEIGHBOURHOOD_ADMIN"
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