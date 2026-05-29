"use client"
import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import CameraFeed from "./CameraFeed"

interface CameraCardProps {
    name: string;
    rtspUrl?: string;
}

export default function CameraCard({ name, rtspUrl }: CameraCardProps) {
    const streamUrl = rtspUrl ? `${process.env.NEXT_PUBLIC_AI_URL}/stream?url=${encodeURIComponent(rtspUrl)}` : null;
    const streamHealthUrl = rtspUrl ? `${process.env.NEXT_PUBLIC_AI_URL}/stream/health?url=${encodeURIComponent(rtspUrl)}` : null;
    const [streamHealth, setStreamHealth] = useState<{ url: string | null; available: boolean; error: boolean }>({
        url: null,
        available: false,
        error: false,
    })
    const [streamImage, setStreamImage] = useState<{ url: string | null; loaded: boolean; error: boolean }>({
        url: null,
        loaded: false,
        error: false,
    })

    useEffect(() => {
        if (!streamHealthUrl) return

        const controller = new AbortController()

        const checkStreamHealth = async () => {
            try {
                const response = await fetch(streamHealthUrl, { signal: controller.signal })
                if (!response.ok) throw new Error("Health check failed")
                const data = await response.json()
                setStreamHealth({ url: streamUrl, available: Boolean(data.available), error: false })
            } catch {
                if (!controller.signal.aborted) {
                    setStreamHealth({ url: streamUrl, available: false, error: true })
                }
            }
        }

        void checkStreamHealth()
        return () => controller.abort()
    }, [streamHealthUrl, streamUrl])

    const streamOnline =
        Boolean(streamUrl) &&
        streamHealth.url === streamUrl &&
        streamHealth.available &&
        !streamHealth.error;

    const effectiveStatus = streamOnline ? "online" : "offline"

    const feedContent = (
        <div className="aspect-video bg-muted rounded-md overflow-hidden flex items-center justify-center relative">
            {streamUrl ? (
                <>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    {/* <img
                        key={streamUrl}
                        src={streamUrl}
                        alt={`Live feed: ${name}`}
                        className={streamImage.error ? "hidden" : "w-full h-full object-cover rounded-md"}
                        onLoad={() => setStreamImage({ url: streamUrl, loaded: true, error: false })}
                        onError={() => setStreamImage({ url: streamUrl, loaded: false, error: true })}
                    /> */}

                    <CameraFeed streamPath="tapo-camera" host="localhost" />


                    {!(streamHealth.url === streamUrl && streamHealth.available && !streamHealth.error) && (
                        <span className="absolute inset-0 flex items-center justify-center text-xs text-muted-foreground">
                            {streamHealth.error ? "Stream unavailable" : "Connecting..."}
                        </span>
                    )}
                </>
            ) : (
                <span className="text-xs text-muted-foreground">No stream configured</span>
            )}
        </div>
    )

    return (
        <Dialog>
            <DialogTrigger asChild>
                <Card className="cursor-pointer hover:ring-2 hover:ring-primary/50 transition-all">
                    <CardHeader className="flex flex-row items-center justify-between p-4">
                        <CardTitle className="text-sm font-medium">{name}</CardTitle>
                        <Badge variant={effectiveStatus === "online" ? "success" : "destructive"}>
                            {effectiveStatus}
                        </Badge>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                        {feedContent}
                    </CardContent>
                </Card>
            </DialogTrigger>
            <DialogContent className="max-w-4xl w-full">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        {name}
                        <Badge variant={effectiveStatus === "online" ? "success" : "destructive"}>
                            {effectiveStatus}
                        </Badge>
                    </DialogTitle>
                </DialogHeader>
                {feedContent}
            </DialogContent>
        </Dialog>
    )
}