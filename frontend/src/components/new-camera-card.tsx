"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

interface NewCameraCardProps {
  onClose: () => void;
  onAcknowledge: (data: { cameraLocation: string; rtspUrl: string }) => void;
}

export function NewCameraCard({ onClose, onAcknowledge }: NewCameraCardProps) {
  const [cameraLocation, setCameraLocation] = useState("");
  const [rtspUrl, setRtspUrl] = useState("");

  const handleSubmit = () => {
    onAcknowledge({ cameraLocation, rtspUrl });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md bg-white rounded-2xl shadow-xl">
        <CardHeader className="relative flex items-center justify-center pb-2">
          <button
            onClick={onClose}
            className="absolute left-4 top-4 text-gray-500 hover:text-gray-800 transition-colors"
          >
            <X size={20} />
          </button>
          <CardTitle className="text-xl font-bold text-center">
            New Camera
          </CardTitle>
        </CardHeader>

        <CardContent className="flex flex-col gap-5 pt-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="camera-location" className="text-sm font-medium">
              Camera Location
            </Label>
            <Input
              id="camera-location"
              placeholder="Enter Camera Location"
              value={cameraLocation}
              onChange={(e) => setCameraLocation(e.target.value)}
              className="bg-gray-50 border-gray-200"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="rtsp-url" className="text-sm font-medium">
              RTSP URL
            </Label>
            <Input
              id="rtsp-url"
              placeholder="Enter RTSP URL"
              value={rtspUrl}
              onChange={(e) => setRtspUrl(e.target.value)}
              className="bg-gray-50 border-gray-200"
            />
          </div>

          <Button
            onClick={handleSubmit}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white rounded-full font-medium"
          >
            Acknowledge
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}