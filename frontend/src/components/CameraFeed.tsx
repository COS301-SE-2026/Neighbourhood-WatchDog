import { useEffect, useRef } from "react";


interface CameraFeedProps {
    streamPath?: string;
    host?: string;
}


export default function CameraFeed({
    streamPath = "tapo-camera",
    host = "localhost"
}: CameraFeedProps) {

    const videoRef = useRef<HTMLVideoElement | null>(null);


    useEffect(() => {
        const whepUrl = `http://${host}:8889/${streamPath}/whep`;

        let pc: RTCPeerConnection | null = null;

        async function connect(): Promise<void> {

            pc = new RTCPeerConnection({
                iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
            });

            pc.ontrack = (event: RTCTrackEvent) => {
                if (videoRef.current) {
                    videoRef.current.srcObject = event.streams[0];
                }
            };

            pc.addTransceiver("video", {
                direction: "recvonly"
            });

            pc.addTransceiver("audio", {
                direction: "recvonly"
            });


            const offer = await pc.createOffer();

            await pc.setLocalDescription(offer);

            const response = await fetch(whepUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/sdp"
                },
                body: pc.localDescription?.sdp
            });

            if (!response.ok) {
                console.error("WHEP request failed", response.status);
                return;
            }


            const sdp = await response.text()


            await pc.setRemoteDescription({
                type: "answer",
                sdp
            });
        }


        connect();


        return () => {
            if (pc) {
                pc.close();
            }
        }
    }, [streamPath, host]);



    return (
        <video ref={videoRef}
               autoPlay
               muted
               playsInline
               style={{
                width: "100%",
                borderRadius: "8px"
               }}
            />
    );
}