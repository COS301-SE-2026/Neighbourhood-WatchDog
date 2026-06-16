"use client"
import { useEffect, useRef, useState } from "react";
import { useCameraAnnotations } from "@/hooks/use-camera-annotations";

interface AnnotatedCameraFeedProps {
  readonly streamPath: string;
  readonly cameraId: string;
  readonly host?: string;
  readonly port?: number;
}

export default function AnnotatedCameraFeed({
  streamPath,
  cameraId,
  host = "localhost",
  port = 8889,
}: AnnotatedCameraFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { annotations, connected } = useCameraAnnotations(cameraId);
  const [videoWidth, setVideoWidth] = useState(0);
  const [videoHeight, setVideoHeight] = useState(0);

  // Extracted: set video dimensions from a loaded video element
  function applyVideoDimensions(video: HTMLVideoElement) {
    if (video.videoWidth > 0) {
      setVideoWidth(video.videoWidth);
      setVideoHeight(video.videoHeight);
    }
  }

  // WebRTC connection setup
  useEffect(() => {
    const whepUrl = `http://${host}:${port}/${streamPath}/whep`;
    let pc: RTCPeerConnection;

    // Extracted outside connect() to reduce nesting depth
    function handleTrack(event: RTCTrackEvent) {
      const video = videoRef.current;
      if (!video) return;
      video.onloadedmetadata = () => applyVideoDimensions(video);
      video.srcObject = event.streams[0];
      applyVideoDimensions(video);
    }

    async function connect() {
      pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });

      pc.ontrack = handleTrack;   // ← just a reference, no inline nesting

      pc.addTransceiver("video", { direction: "recvonly" });
      pc.addTransceiver("audio", { direction: "recvonly" });

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const response = await fetch(whepUrl, {
        method: "POST",
        headers: { "Content-Type": "application/sdp" },
        body: pc.localDescription!.sdp,
      });

      const answerSdp = await response.text();
      await pc.setRemoteDescription(
        new RTCSessionDescription({ type: "answer", sdp: answerSdp })
      );
    }

    connect().catch(console.error);
    return () => { if (pc) pc.close(); };
  }, [streamPath, host, port]);

  // Draw annotations on canvas overlay
  useEffect(() => {
    if (!canvasRef.current || !videoWidth || !videoHeight) return;

    const canvas = canvasRef.current;
    canvas.width = videoWidth;
    canvas.height = videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!annotations?.tracks || annotations.tracks.length === 0) return;

    for (const track of annotations.tracks) {
      const [left, top, right, bottom] = track.bbox;
      const w = right - left;
      const h = bottom - top;

      ctx.strokeStyle = "#00ff00";
      ctx.lineWidth = 2;
      ctx.strokeRect(left, top, w, h);

      const label = `ID ${track.track_id}  ${(track.confidence * 100).toFixed(0)}%`;
      ctx.font = "bold 14px Arial";
      const textW = ctx.measureText(label).width;
      const labelY = top > 24 ? top - 6 : bottom + 18;
      ctx.fillStyle = "rgba(0, 0, 0, 0.55)";
      ctx.fillRect(left, labelY - 14, textW + 8, 18);
      ctx.fillStyle = "#00ff00";
      ctx.fillText(label, left + 4, labelY);
    }
  }, [annotations, videoWidth, videoHeight]);

  return (
    <div className="relative aspect-video bg-muted rounded-md overflow-hidden">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-contain"
      />
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ objectFit: "contain" }}
      />
      {/* Annotation WebSocket status dot */}
      <div
        className={`absolute top-2 right-2 w-2 h-2 rounded-full ${
          connected ? "bg-green-400" : "bg-red-500"
        }`}
        title={connected ? "Annotations live" : "Annotations disconnected"}
      />
    </div>
  );
}
