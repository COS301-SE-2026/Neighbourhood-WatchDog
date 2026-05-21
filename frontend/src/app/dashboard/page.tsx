"use client"
import CameraCard from "@/components/CameraCard"
import { NewCameraCard } from "@/components/new-camera-card"
import { useState } from "react"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function Dashboard() {

    const [showCard, setShowCard] = useState(false);

    const handleAcknowledge = (data: { cameraLocation: string; rtspUrl: string }) => {
        console.log("New camera added:", data);
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
                <CameraCard name="Camera 1 - Backyard" status="offline" />
                {/* <CameraCard name="Camera 2 - Bedroom 1" status="online" /> */}

                <CameraCard name="Camera 2 - Office Room 1" status="online" rtspUrl="rtsp://Intrepid:password1234@172.20.10.2:554/stream2"/>
                <CameraCard name="Camera 5 - Living Room" status="online" />
                <CameraCard name="Camera 3 - Bedroom 2" status="online" />
                <CameraCard name="Camera 4 - Kitchen" status="online" />
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