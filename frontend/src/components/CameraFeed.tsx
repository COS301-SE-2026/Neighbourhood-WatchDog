"use client"
import { useEffect, useRef } from "react";


interface CameraFeedProps {

    streamPath: string // "tapo-camera"
    host?: string // "localhost"
    port?: number // 8889

}


export default function CameraFeed({

    streamPath,
    host = "localhost",
    port = 8889

}: CameraFeedProps) {

    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {

        const whepUrl = `http://${host}:${port}/${streamPath}/whep`;

        let pc: RTCPeerConnection;
        async function connect() {

            pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302"}] });

            pc.ontrack = (event) => {
                if (videoRef.current) videoRef.current.srcObject = event.streams[0];
            }

            pc.addTransceiver("video", {direction: "recvonly"});
            pc.addTransceiver("audio", {direction: "recvonly"});


            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);

            const response = await fetch(whepUrl, {
                method: "POST",
                headers: {"Content-Type": "application/sdp"},
                body: pc.localDescription!.sdp
            });


            if (!response.ok) {
                console.error("WHEP handshake failed", response.status);
                return;

            }

            const sdp = await response.text();
            await pc.setRemoteDescription({ type: "answer", sdp});



        }


        connect().catch(console.error);

        return () => {
            if (pc) pc.close();
        }

    }, [streamPath, host, port])


    return (

        <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover rounded-md"/>
    )
}