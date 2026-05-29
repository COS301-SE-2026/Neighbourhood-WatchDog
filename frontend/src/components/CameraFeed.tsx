"use client"

interface CameraFeedProps {
    streamUrl: string;
}

export default function CameraFeed({ streamUrl }: CameraFeedProps) {
    return (
        <img
            src={streamUrl}
            alt="Live camera feed"
            className="w-full h-full object-cover rounded-md"
        />
    )
}