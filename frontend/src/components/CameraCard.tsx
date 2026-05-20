"use client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

interface CameraCardProps {
    name: string;
    status: "online" | "offline";
    rtspUrl?: string;
}

export default function CameraCard({ name, status, rtspUrl }: CameraCardProps) {
    const streamUrl = rtspUrl ? `http://localhost:8001/stream?url=${encodeURIComponent(rtspUrl)}` : null;

    const feedContent = (
        <div className="aspect-video bg-muted rounded-md overflow-hidden flex items-center justify-center">
            {streamUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                    src={streamUrl}
                    alt={`Live feed: ${name}`}
                    className="w-full h-full object-cover rounded-md"
                />
            ) : (
                <span className="text-xs text-muted-foreground">
                    {status === "offline" ? "Camera offline" : "No stream configured"}
                </span>
            )}
        </div>
    );

    return (
        <Dialog>
            <DialogTrigger asChild>
                <Card className="cursor-pointer hover:ring-2 hover:ring-primary/50 transition-all">
                    <CardHeader className="flex flex-row items-center justify-between p-4">
                        <CardTitle className="text-sm font-medium">{name}</CardTitle>
                        <Badge variant={status === "online" ? "success" : "destructive"}>
                            {status}
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
                        <Badge variant={status === "online" ? "success" : "destructive"}>
                            {status}
                        </Badge>
                    </DialogTitle>
                </DialogHeader>
                {feedContent}
            </DialogContent>
        </Dialog>
    )
}