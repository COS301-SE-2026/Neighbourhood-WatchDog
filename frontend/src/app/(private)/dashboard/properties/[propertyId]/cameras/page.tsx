"use client";

import { useEffect, useState } from "react";
import { CameraOff, LoaderCircle, Plus } from "lucide-react";
import { toast } from "sonner";

import type { Camera } from "@/lib/validators/camera";
import {
    addCamera as apiAddCamera,
    fetchCameras as apiFetchCameras
} from "@/lib/api/camera";

import { NewCameraCard } from "@/components/new-camera-card";
import CameraCard from "@/components/CameraCard";
import { usePropertyContext } from "@/hooks/use-property-context";

interface CameraProp {
    id: string;
    name: string;
    visibility: Camera["visibility"],
    enabled: boolean
    location: string
    rtspUrl?: string;

}

export default function PropertyCamerasPage() {
    const { activeContext, isLoading: isLoadingProperty } = usePropertyContext();

    const [cameras, setCameras] = useState<CameraProp[]>([]);
    const [resolvedPropertyId, setResolvedPropertyId] = useState<string | null>(null);
    const [showCard, setShowCard] = useState(false);

    const propertyId = activeContext?.propertyId ?? null;

    const isLoadingCameras = propertyId !== null && resolvedPropertyId !== propertyId;

    useEffect(() => {
        if (!propertyId) {
            return;
        }

        let cancelled = false;

        let firstLoad = true;
        const loadCameras = async () => {
            try {
                const data = await apiFetchCameras(propertyId);
                if (cancelled) return;

                setCameras(
                    data.map((camera) => ({
                        id: camera.id, 
                        name: camera.name, 
                        location: camera.location, 
                        visibility: camera.visibility, 
                        enabled: camera.enabled, 
                        edgeAgentAvailable: camera.edge_agent_available
                    }))
                );
                setResolvedPropertyId(propertyId);
            }catch(error) {
                if (cancelled) return;
                console.error("Failed to fetch cameras", error);

                if (firstLoad) {
                    toast.error("Failed to load cameras");
                    setCameras([]);
                    setResolvedPropertyId(propertyId);
                }
            }
            finally{
                firstLoad = false;
            }
        };

        void loadCameras();


        return () => {
            cancelled = true;

        }

    }, [propertyId]);

    const handleAddCamera = async (data: { name: string, location: string, rtspUrl: string }) => {
        if (!propertyId) {
            toast.error("Select a property before adding a camera");
            return;
        }

        try {
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
                    edgeAgentAvailable: null
                }
            ]);
            setShowCard(false);
        }
        catch (error) {
            console.error("Failed to add camera", error);
            toast.error("Failed to add camera");
        }
    };

    if (isLoadingProperty) {
        return (
            <main className="min-h-full w-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
                <div className="flex min-h-64 items-center justify-center">
                    <LoaderCircle className="size-6 animate-spin text-brand-ash" />
                </div>
            </main>
        )
    }

    if (!activeContext) {
        return (
            <main className="min-h-full w-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
                <div className="flex min-h-64 flex-col items-center justify-center text-center">
                    <CameraOff className="mb-4 size-8 text-brand-ash/60" />
                    <h2 className="text-lg font-semibold">
                        No property selected
                    </h2>
                    <p className="mt-2 text-sm text-brand-ash">
                        Select a property to view its cameras.
                    </p>
                </div>
            </main>
        );
    }

    const enabledCameraCount = cameras.filter((camera) => camera.enabled).length;
    const disabledCameraCount = cameras.filter((camera) => !camera.enabled).length;

    return (
        <main className="min-h-full w-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
            <div className="max-w-full">
                <header className="mb-7 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <p className="text-sm text-brand-ash">
                            {activeContext.address}
                        </p>
                        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
                            Cameras
                        </h1>
                    </div>

                    <button
                        type="button"
                        onClick={() => setShowCard(true)}
                        className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-brand-green px-3.5 text-sm font-medium text-brand-void transition-colors hover:bg-brand-green"
                    >
                        <Plus className="size-4" />
                        Add camera
                    </button>
                </header>

                <div className="mb-8 flex flex-wrap items-center gap-x-5 gap-y-2 border-y border-border py-3 text-sm">
                    <span className="text-brand-ash">
                        <span className="font-medium text-brand-frost">{enabledCameraCount}</span>{" "}
                        enabled
                    </span>

                    <span className="flex items-center gap-2 text-brand-ash">
                        <span className="size-1.5 rounded-full bg-brand-green" />
                        <span>
                            <span className="font-medium text-brand-frost">{disabledCameraCount}</span>{" "}
                            disabled
                        </span>
                    </span>
                </div>

                <section aria-labelledby="camera-feeds-heading">
                    <div className="mb-4">
                        <h2 id="camera-feeds-heading" className="text-base font-semibold">
                            Cameras
                        </h2>
                        <p className="mt-1 text-sm text-brand-ash">
                            Cameras configured for this property.
                        </p>
                    </div>

                    {isLoadingCameras ? (
                        <div className="flex min-h-64 items-center justify-center rounded-lg border border-border bg-brand-depth">
                            <LoaderCircle className="size-6 animate-spin text-brand-ash" />
                        </div>
                    ) : cameras.length === 0 ? (
                        <div className="flex min-h-72 flex-col items-center justify-center rounded-lg border border-dashed border-border bg-brand-depth px-6 py-12 text-center">
                            <CameraOff className="mb-4 size-8 text-brand-ash/60" />
                            <h2 className="text-base font-semibold">No cameras added yet</h2>
                            <p className="mt-2 max-w-sm text-sm text-brand-ash">
                                Add a camera to this property to start monitoring it.
                            </p>
                            <button
                                type="button"
                                onClick={() => setShowCard(true)}
                                className="mt-6 inline-flex h-9 items-center justify-center gap-2 rounded-md bg-brand-green px-3.5 text-sm font-medium text-brand-void transition-colors hover:bg-brand-green"
                            >
                                <Plus className="size-4" />
                                Add your first camera
                            </button>
                        </div>
                    ) : (
                        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                            {cameras.map((camera) => (
                                <CameraCard
                                    key={camera.id}
                                    id={camera.id}
                                    name={camera.name}
                                    location={camera.location}
                                    visibility={camera.visibility}
                                    enabled={camera.enabled}
                                    edgeAgentAvailable={camera.edgeAgentAvailable}
                                    userRole={activeContext.role === "Neighbourhood Admin" ? "NEIGHBOURHOOD_ADMIN" : "RESIDENT"}
                                    onDeleted={(deletedCameraId) => {
                                        setCameras((currentCameras) =>
                                            currentCameras.filter(
                                                (currentCamera) => currentCamera.id !== deletedCameraId
                                            )
                                        );
                                    }}
                                />
                            ))}
                        </div>
                    )}
                </section>
            </div>

            {showCard && (
                <NewCameraCard
                    onClose={() => setShowCard(false)}
                    onAcknowledge={handleAddCamera}
                />
            )}
        </main>
    );
}
