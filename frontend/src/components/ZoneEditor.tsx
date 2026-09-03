"use client";
import { useRef, useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";



interface Point { x: number; y: number }


interface ZoneEditorProps {

  readonly videoRef: React.RefObject<HTMLVideoElement | null>;
  readonly onSave: (polygon: number[][], name: string) => Promise<void>;
  readonly onCancel: () => void;

}


export function ZoneEditor({ videoRef, onSave, onCancel }: ZoneEditorProps) {

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [saving, setSaving] = useState(false);
  const [hasFrame, setHasFrame] = useState(false);

  //capture a still frame from the live video as canvas background
  const captureFrame = useCallback(() => {

    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) return;

    const w = video.videoWidth || video.clientWidth || 640;
    const h = video.videoHeight || video.clientHeight || 360;

    canvas.width = w;
    canvas.height = h;

    const ctx = canvas.getContext("2d");

    if (!ctx) return;

    if (video.videoWidth > 0) {

      ctx.drawImage(video, 0, 0, w, h);
      setHasFrame(true);

    } else {

      const styles = getComputedStyle(document.documentElement);
      ctx.fillStyle =
        styles.getPropertyValue("--color-abyss").trim() || "#0D0D0D";
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle =
        styles.getPropertyValue("--color-ash").trim() || "#A3A3A3";
      ctx.font = "14px Arial";
      ctx.fillText("No video signal - drawing on blank frame", 20, h / 2);
      setHasFrame(true);

    }
    setPoints([]);
  }, [videoRef]);



  //auto capture on mount
  useEffect(() => { captureFrame() }, [captureFrame]);

  const redraw = useCallback(() => {

    const canvas = canvasRef.current;
    if (!canvas || !hasFrame) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;


    //restoring the captured frame  - redrawing from live video
    const video = videoRef.current;
    if (video && video.videoWidth > 0) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    }

    if (points.length === 0) return;

    const w = canvas.width;
    const h = canvas.height;

    //semi-transparent overlay outside polygon
    const styles = getComputedStyle(document.documentElement);
    const cautionColour =
      styles.getPropertyValue("--color-caution").trim() || "#F59E0B";
    const frostColour =
      styles.getPropertyValue("--color-frost").trim() || "#F5F5F5";

    ctx.beginPath();
    ctx.strokeStyle = cautionColour;
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 3]);
    ctx.moveTo(points[0].x * w, points[0].y * h);

    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x * w, points[i].y * h);
    }

    if (points.length > 2) ctx.lineTo(points[0].x * w, points[0].y * h);

    ctx.stroke();


    for (const p of points) {

      ctx.beginPath();
      ctx.fillStyle = cautionColour;
      ctx.arc(p.x * w, p.y * h, 5, 0, Math.PI * 2);
      ctx.fill();
    }

    //first point =  close target
    ctx.beginPath();
    ctx.strokeStyle = frostColour;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([]);
    ctx.arc(points[0].x * w, points[0].y * h, 10, 0, Math.PI * 2);
    ctx.stroke();
  }, [points, hasFrame, videoRef]);



  useEffect(() => { redraw() }, [redraw]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width;
    const ny = (e.clientY - rect.top) / rect.height;


    if (points.length >= 3) {

      const dx = nx - points[0].x;
      const dy = ny - points[0].y;

      if (Math.hypot(dx * dx + dy * dy) < 0.03) {
        handleSave();
        return;

      }
    }

    setPoints(prev => [...prev, { x: nx, y: ny }]);
  }

  const handleSave = async () => {

    if (points.length < 3) return;
    setSaving(true);
    try {

      await onSave(points.map(p => [p.x, p.y]), `Zone ${Date.now()}`);
      setPoints([]);
    } finally {

      setSaving(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>Click to add vertices. Click near the first circle to close and save the zone.</span>
        <Button size="sm" variant="ghost" className="h-6 text-xs" onClick={captureFrame}>
          Refresh frame
        </Button>
      </div>
      <div className="relative rounded-md overflow-hidden">
        <canvas
          ref={canvasRef}
          className="w-full cursor-crosshair"
          onClick={handleClick}
        />
      </div>
      <div className="flex gap-2">
        <Button size="sm" onClick={handleSave} disabled={points.length < 3 || saving}>
          {saving ? "Saving…" : `Save zone (${points.length} pts)`}
        </Button>
        <Button size="sm" variant="outline" onClick={() => setPoints([])}>Clear</Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  )
}
