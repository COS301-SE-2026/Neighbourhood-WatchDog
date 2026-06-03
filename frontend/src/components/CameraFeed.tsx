"use client"
import { useEffect, useRef, useState } from "react";
import { useCameraAnnotations, type AnnotationData } from "@/hooks/use-camera-annotations";

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
  const { annotations } = useCameraAnnotations(cameraId);
  const [videoWidth, setVideoWidth] = useState(0);
  const [videoHeight, setVideoHeight] = useState(0);

  // WebRTC connection setup
  useEffect(() => {
    const whepUrl = `http://${host}:${port}/${streamPath}/whep`;

    let pc: RTCPeerConnection;
    async function connect() {
      pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });

      pc.ontrack = (event) => {
        if (videoRef.current) {

          videoRef.current.srcObject = event.streams[0];

          // video dimensions
          videoRef.current.onloadedmetadata = () => {

            setVideoWidth(videoRef.current!.videoWidth);
            setVideoHeight(videoRef.current!.videoHeight);
          };


        }
      };

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
      await pc.setRemoteDescription(new RTCSessionDescription({ type: "answer", sdp: answerSdp }));


    }

    connect().catch(console.error);

    return () => {
      if (pc) pc.close();
    };

  }, [streamPath, host, port]);

  // draw annotations on canvas overlay
  useEffect(() => {
    if (!canvasRef.current || !videoWidth || !videoHeight) return;

    const canvas = canvasRef.current;
    canvas.width = videoWidth;
    canvas.height = videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (annotations?.tracks) {
      annotations.tracks.forEach((track) => {
        const [left, top, right, bottom] = track.bbox;

        // draw bounding box
        ctx.strokeStyle = "#00ff00";
        ctx.lineWidth = 2;
        ctx.strokeRect(left, top, right - left, bottom - top);

        // draw track ID and confidence
        const label = `ID: ${track.track_id} | ${(track.confidence * 100).toFixed(0)}%`;
        ctx.fillStyle = "#00ff00";
        ctx.font = "14px Arial";
        ctx.fillText(label, left, top - 5);
      });
    }
  }, [annotations, videoWidth, videoHeight]);

  return (
    <div className="relative aspect-video bg-muted rounded-md overflow-hidden">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="w-full h-full object-cover"
      />
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
      />
    </div>
  );
}