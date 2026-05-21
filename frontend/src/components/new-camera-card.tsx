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
  const [touched, setTouched] = useState({ cameraLocation: false, rtspUrl: false });

  const errors = {
    cameraLocation: touched.cameraLocation && cameraLocation.trim() === "",
    rtspUrl: touched.rtspUrl && rtspUrl.trim() === "",
  };

  const isValid = cameraLocation.trim() !== "" && rtspUrl.trim() !== "";

  const handleSubmit = () => {
    setTouched({ cameraLocation: true, rtspUrl: true });
    if (!isValid) return;
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
              onBlur={() => setTouched((t) => ({ ...t, cameraLocation: true }))}
              className={`bg-gray-50 border-gray-200 ${errors.cameraLocation ? "border-red-500 focus-visible:ring-red-400" : ""}`}
            />
            {errors.cameraLocation && (
              <p className="text-xs text-red-500">Camera location is required.</p>
            )}
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
              onBlur={() => setTouched((t) => ({ ...t, rtspUrl: true }))}
              className={`bg-gray-50 border-gray-200 ${errors.rtspUrl ? "border-red-500 focus-visible:ring-red-400" : ""}`}
            />
            {errors.rtspUrl && (
              <p className="text-xs text-red-500">RTSP URL is required.</p>
            )}
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!isValid}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white rounded-full font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Acknowledge
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}