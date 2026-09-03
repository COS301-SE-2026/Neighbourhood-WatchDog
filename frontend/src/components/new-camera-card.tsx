"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

interface NewCameraCardProps {
  onClose: () => void;
  onAcknowledge: (data: { name: string, location: string; rtspUrl: string }) => void;
}

export function NewCameraCard({ onClose, onAcknowledge }: NewCameraCardProps) {
  const [name, setName] = useState("")
  const [location, setLocation] = useState("");
  const [rtspUrl, setRtspUrl] = useState("");
  const [touched, setTouched] = useState({ name: false, location: false, rtspUrl: false });

  const errors = {
    name: touched.name && name.trim() === "",
    location: touched.location && location.trim() === "",
    rtspUrl: touched.rtspUrl && rtspUrl.trim() === "",
  };

  const isValid = location.trim() !== "" && rtspUrl.trim() !== "";

  const handleSubmit = () => {
    setTouched({ name: true, location: true, rtspUrl: true });
    if (!isValid) return;
    onAcknowledge({name ,location, rtspUrl });
  };

  return (
    <div className="fixed inset-0 bg-brand-void/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md bg-brand-depth rounded-xl shadow-xl">
        <CardHeader className="relative flex items-center justify-center pb-2">
          <button
            onClick={onClose}
            className="absolute left-4 top-4 text-brand-ash hover:text-ink transition-colors"
          >
            <X size={20} />
          </button>
          <CardTitle className="text-xl font-bold text-center">
            New Camera
          </CardTitle>
        </CardHeader>

        <CardContent className="flex flex-col gap-5 pt-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="camera-name" className="text-sm font-medium">
              Camera Name
            </Label>
            <Input
              id="camera-name"
              placeholder="Enter Camera Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="bg-mist/10 border-mist/40"
            />
            {errors.name && <p className="text-xs text-threat">Camera name is required</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="camera-location" className="text-sm font-medium">
              Camera Location
            </Label>
            <Input
              id="camera-location"
              placeholder="Enter Camera Location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, cameraLocation: true }))}
              className={`bg-mist/10 border-mist/40 ${errors.location ? "border-threat focus-visible:ring-threat" : ""}`}
            />
            {errors.location && (
              <p className="text-xs text-threat">Camera location is required.</p>
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
              className={`bg-mist/10 border-mist/40 ${errors.rtspUrl ? "border-threat focus-visible:ring-threat" : ""}`}
            />
            {errors.rtspUrl && (
              <p className="text-xs text-threat">RTSP URL is required.</p>
            )}
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!isValid}
            className="w-full bg-brand-pulse hover:bg-sky text-brand-frost rounded-full font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Acknowledge
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}