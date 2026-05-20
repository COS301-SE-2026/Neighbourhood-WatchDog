import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

function CameraCard({ name, status }: { name: string; status: "online" | "offline" }) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between p-4">
                <CardTitle className="text-sm font-medium">{name}</CardTitle>
                <Badge variant={status === "online" ? "default" : "destructive"}>
                    {status}
                </Badge>
            </CardHeader>
            <CardContent className="p-4 pt-0">
                {/* camera feed / placeholder goes here */}
                <div className="aspect-video bg-muted rounded-md" />
            </CardContent>
        </Card>
    )
}