"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { CameraCoverageEditor } from "@/components/CameraCoverageEditor";
import type { CameraCoverageInput } from "@/lib/validators/camera-coverage";

interface NewCameraData {
  name: string;
  location: string;
  rtspUrl: string;
  coverage?: CameraCoverageInput;
}

interface NewCameraCardProps {
  onClose: () => void;
  onAcknowledge: (data: NewCameraData) => void;
  propertyLatitude: number | null;
  propertyLongitude: number | null;
}

export function NewCameraCard({
  onClose,
  onAcknowledge,
  propertyLatitude,
  propertyLongitude,
}: NewCameraCardProps) {
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [rtspUrl, setRtspUrl] = useState("");
  const [configureCoverage, setConfigureCoverage] = useState(false);
  const [coverage, setCoverage] = useState<CameraCoverageInput | undefined>();
  const [touched, setTouched] = useState({
    name: false,
    location: false,
    rtspUrl: false,
  });

  const errors = {
    name: touched.name && name.trim() === "",
    location: touched.location && location.trim() === "",
    rtspUrl: touched.rtspUrl && rtspUrl.trim() === "",
  };

  const isValid =
    name.trim() !== "" &&
    location.trim() !== "" &&
    rtspUrl.trim() !== "" &&
    (!configureCoverage || coverage !== undefined);

  const handleSubmit = () => {
    setTouched({ name: true, location: true, rtspUrl: true });

    if (!isValid) {
      return;
    }

    onAcknowledge({
      name: name.trim(),
      location: location.trim(),
      rtspUrl: rtspUrl.trim(),
      ...(configureCoverage && coverage ? { coverage } : {}),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-brand-void/50 p-4">
      <Card className="my-4 max-h-[calc(100vh-2rem)] w-full max-w-2xl overflow-y-auto rounded-xl bg-brand-depth shadow-xl">
        <CardHeader className="relative flex items-center justify-center pb-2">
          <button
            type="button"
            onClick={onClose}
            aria-label="Close new camera form"
            title="Close new camera form"
            className="absolute left-4 top-4 text-brand-ash transition-colors hover:text-brand-frost"
          >
            <X size={20} aria-hidden="true" />
          </button>
          <CardTitle className="text-center text-xl font-bold">
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
              onChange={(event) => setName(event.target.value)}
              onBlur={() => setTouched((current) => ({ ...current, name: true }))}
              className={`border-mist/40 bg-mist/10 ${errors.name ? "border-threat focus-visible:ring-threat" : ""}`}
            />
            {errors.name && (
              <p className="text-xs text-threat">Camera name is required.</p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="camera-location" className="text-sm font-medium">
              Camera Location
            </Label>
            <Input
              id="camera-location"
              placeholder="Enter Camera Location"
              value={location}
              onChange={(event) => setLocation(event.target.value)}
              onBlur={() => setTouched((current) => ({ ...current, location: true }))}
              className={`border-mist/40 bg-mist/10 ${errors.location ? "border-threat focus-visible:ring-threat" : ""}`}
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
              onChange={(event) => setRtspUrl(event.target.value)}
              onBlur={() => setTouched((current) => ({ ...current, rtspUrl: true }))}
              className={`border-mist/40 bg-mist/10 ${errors.rtspUrl ? "border-threat focus-visible:ring-threat" : ""}`}
            />
            {errors.rtspUrl && (
              <p className="text-xs text-threat">RTSP URL is required.</p>
            )}
          </div>

          <label className="flex items-center gap-2 text-sm text-brand-frost">
            <input
              type="checkbox"
              checked={configureCoverage}
              onChange={(event) => {
                const enabled = event.target.checked;
                setConfigureCoverage(enabled);
                if (!enabled) {
                  setCoverage(undefined);
                }
              }}
              className="size-4 accent-brand-green"
            />
            Configure camera POV now (optional)
          </label>

          {configureCoverage && (
            <CameraCoverageEditor
              propertyLatitude={propertyLatitude}
              propertyLongitude={propertyLongitude}
              value={coverage}
              onChange={setCoverage}
            />
          )}

          <Button
            onClick={handleSubmit}
            disabled={!isValid}
            className="w-full rounded-full bg-brand-green font-medium text-brand-void hover:bg-brand-green disabled:cursor-not-allowed disabled:opacity-50"
          >
            Add camera
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}