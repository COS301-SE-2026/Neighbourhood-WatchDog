import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"


interface CameraCardProps {

    name: string;
    status: "online" | "offline";
    rtspUrl?: string;
}

export default function CameraCard({ name, status, rtspUrl }: CameraCardProps) {
    const streamUrl = rtspUrl ? `http://localhost:8000/api/stream?url=${encodeURIComponent(rtspUrl)}` : null;

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between p-4">
                <CardTitle className="text-sm font-medium">{name}</CardTitle>
                <Badge variant={status === "online" ? "success" : "destructive"}>
                    {status}
                </Badge>
            </CardHeader>
            <CardContent className="p-4 pt-0">
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
            </CardContent>
        </Card>
    )
}