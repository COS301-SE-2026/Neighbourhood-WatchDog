"use client"
import CameraCard from "@/components/CameraCard"
import type { Camera } from "@/lib/validators/camera"
import { useAlerts } from "@/hooks/use-alerts"
import { toast } from "sonner"
import { useEffect, useState } from "react"
import { CameraOff, LoaderCircle,Plus } from "lucide-react";

import { addCamera as apiAddCamera, fetchCameras as apiFetchCameras } from "@/lib/api/camera"
import { NewCameraCard } from "@/components/new-camera-card"
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



export default function Dashboard() {
    const [isLoadingCameras, setIsLoadingCameras] = useState(true);
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
        if (!propertyId) {
            return;
        }

        // eslint-disable-next-line react-hooks/set-state-in-effect
        setIsLoadingCameras(true);

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
            })
            .finally(() => {
            setIsLoadingCameras(false);
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

            {isLoadingCameras ? (
                <div className="flex min-h-64 items-center justify-center">
                    <LoaderCircle className="h-6 w-6 animate-spin text-primary" />
                </div>
                ) : cameras.length === 0 ? (
                <div className="flex min-h-72 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card px-6 py-12 text-center">
                    <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                    <CameraOff className="h-7 w-7 text-primary" />
                    </div>

                    <h2 className="text-lg font-semibold text-foreground">
                    No cameras added yet
                    </h2>

                    <p className="mt-2 max-w-sm text-sm leading-relaxed text-muted-foreground">
                    Add a camera to this property to start monitoring live feeds and receive
                    AI-powered security alerts.
                    </p>

                    <Button
                    onClick={() => setShowCard(true)}
                    className="mt-6 bg-primary text-primary-foreground hover:bg-primary/90"
                    >
                    <Plus className="mr-2 h-4 w-4" />
                    Add your first camera
                    </Button>
                </div>
                ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
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
                )}

            {showCard && (
                <NewCameraCard
                    onClose={() => setShowCard(false)}
                    onAcknowledge={handleAcknowledge}
                />
            )}
        </div>
    )
}