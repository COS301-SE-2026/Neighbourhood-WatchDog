"use client"
import CameraCard from "@/components/CameraCard"

export default function Dashboard() {
    return(
        <div className="w-full p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <CameraCard name="Camera 1 - Backyard" status="offline" />
                <CameraCard name="Camera 2 - Bedroom 1" status="online" />
                <CameraCard name="Camera 5 - Living Room" status="online" />
                <CameraCard name="Camera 3 - Bedroom 2" status="online" />
                <CameraCard name="Camera 4 - Kitchen" status="online" />
            </div>
        </div>
    )
}