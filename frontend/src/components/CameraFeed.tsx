"use client";

import React, { forwardRef, useEffect, useRef, useState } from "react";
import { useCameraAnnotations } from "@/hooks/use-camera-annotations";

export type CameraStreamState = "idle" | "connecting" | "live" | "unavailable";

interface AnnotatedCameraFeedProps {
  readonly streamPath: string;
  readonly cameraId: string;
  readonly whepBaseUrl?: string;
  readonly onStreamStateChange?: (state: CameraStreamState) => void;

}

  function handleConnectionStateChange(pc: RTCPeerConnection, reportState: (state: CameraStreamState) => void){

      if (pc.connectionState === "failed") {
        reportState("unavailable");

      }
  }

const AnnotatedCameraFeed = forwardRef<HTMLVideoElement, AnnotatedCameraFeedProps>(function AnnotatedCameraFeed({ streamPath, cameraId, whepBaseUrl=process.env.NEXT_PUBLIC_MEDIAMTX_WEBRTC_URL ?? "http://localhost:8889", onStreamStateChange,},ref) {
  const internalVideoRef = useRef<HTMLVideoElement>(null);
  const videoRef =(ref as React.RefObject<HTMLVideoElement>) ?? internalVideoRef;

  const canvasRef = useRef<HTMLCanvasElement>(null);

  const { annotations, connected } = useCameraAnnotations(cameraId);

  const [videoWidth, setVideoWidth] = useState(0);
  const [videoHeight, setVideoHeight] = useState(0);

  function applyVideoDimensions(video: HTMLVideoElement){

    if (video.videoWidth > 0) {
      setVideoWidth(video.videoWidth);
      setVideoHeight(video.videoHeight);
    }

  }

  function registerMetadataHandler(video: HTMLVideoElement) {

    video.onloadedmetadata = handleLoadedMetadata.bind(null, video);
  }

  function handleLoadedMetadata(video: HTMLVideoElement) {
    applyVideoDimensions(video);

  }

  function attachVideoStream(video: HTMLVideoElement, stream: MediaStream, reportState: (state: CameraStreamState) => void){
    registerMetadataHandler(video);

    video.srcObject = stream;

    void video.play().catch(() => undefined);

    applyVideoDimensions(video);
    reportState("live");

  }

  

  useEffect(() => {
    const baseUrl = whepBaseUrl.replace(/\/$/, "");
    const whepUrl = `${baseUrl}/${streamPath}/whep`;

    const video = videoRef.current;

    const controller = new AbortController();

    let peerConnection: RTCPeerConnection | null = null;
    let whepSessionUrl: string | null = null;
    let disposed = false;

    const reportState = (state: CameraStreamState) => {

      if (!disposed) {onStreamStateChange?.(state);}
    };

    const connect = async () => {
      reportState("connecting");

      peerConnection = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }],});

      peerConnection.ontrack = (event) => {
        if (!video) return;

        attachVideoStream(video, event.streams[0], reportState);
      };

      peerConnection.onconnectionstatechange = () => {
        if (!peerConnection) return;

        handleConnectionStateChange(peerConnection, reportState);
      };

      peerConnection.addTransceiver("video", { direction: "recvonly" });

      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);

      const response = await fetch(whepUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/sdp",
        },
        body: peerConnection.localDescription?.sdp,
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`WHEP request failed with HTTP ${response.status}`);
      }

      const location = response.headers.get("location");

      if (location) {
        whepSessionUrl = new URL(location, whepUrl).toString();
      }

      const answerSdp = await response.text();

      await peerConnection.setRemoteDescription({
        type: "answer",
        sdp: answerSdp
      });
    };

    void connect().catch((error: unknown) => {

      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }

      console.warn(
        `WEBRTC stream unavailable for camera ${cameraId}:`,
        error
      );

      reportState("unavailable");
    });





    return () => {
      disposed = true;

      controller.abort();

      if (video) video.srcObject = null;
    

      peerConnection?.close();

      if (whepSessionUrl) {
        void fetch(whepSessionUrl, {

          method: "DELETE",
          keepalive: true

        }).catch(() => undefined);
      }
    };
  }, [cameraId, onStreamStateChange, streamPath, videoRef, whepBaseUrl,]);

  useEffect(() => {
    if (!canvasRef.current || !videoWidth || !videoHeight) {
      return;
    }

    const canvas = canvasRef.current;

    canvas.width = videoWidth;
    canvas.height = videoHeight;

    const ctx = canvas.getContext("2d");

    if (!ctx) {
      return;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!annotations?.tracks || annotations.tracks.length === 0) {
      return;
    }

    for (const track of annotations.tracks) {
      const [left, top, right, bottom] = track.bbox;

      const width = right - left;
      const height = bottom - top;

      const isWeapon =
        track.detection_type &&
        track.detection_type.toLowerCase() !== "person";

      const colour = isWeapon ? "#ff0000" : "#00ff00";

      ctx.strokeStyle = colour;
      ctx.lineWidth = 2;
      ctx.strokeRect(left, top, width, height);

      const label = `${track.detection_type ?? "unknown"} ${(
        track.confidence * 100
      ).toFixed(0)}%`;

      ctx.font = "bold 14px Arial";

      const textWidth = ctx.measureText(label).width;

      const labelY = top > 24 ? top - 6 : bottom + 18;

      ctx.fillStyle = "rgba(0, 0, 0, 0.55)";
      ctx.fillRect(left, labelY - 14, textWidth + 8, 18);

      ctx.fillStyle = colour;
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

      <div
        className={`absolute top-2 right-2 w-2 h-2 rounded-full ${
          connected ? "bg-green-400" : "bg-red-500"
        }`}
        title={connected ? "Annotations live" : "Annotations disconnected"}
      />
    </div>
  );
});

AnnotatedCameraFeed.displayName = "AnnotatedCameraFeed";

export default AnnotatedCameraFeed;
