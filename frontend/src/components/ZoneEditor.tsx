"use client"
import React, { useRef, useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";


interface Point {

    x: number;
    y: number

}


interface ZoneEditorProps {

    readonly videoRef: React.RefObject<HTMLVideoElement | null>;
    readonly onSave: (polygon: number[][], name: string) => Promise<void>;
    readonly onCancel: () => void;

}


export function ZoneEditor({ videoRef, onSave, onCancel }: ZoneEditorProps) {

    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [points, setPoints] = useState<Point[]>([]);
    const [saving, setSaving] = useState(false);


    //to draw the polygon, the current one on the canvas
    const draw = useCallback(() => {

        const canvas = canvasRef.current;
        const video = videoRef.current;

        if (!canvas || ! video) return;

        canvas.width = video.videoWidth || video.clientWidth;
        canvas.height = video.height || video.clientHeight;


        const canvasContext = canvas.getContext("2d");
        if (!canvasContext) return;


        canvasContext.clearRect(0, 0, canvas.width, canvas.height);
        if (points.length === 0) return;


        const w = canvas.width;
        const h = canvas.height;



        //drawing the polygon lines.
        canvasContext.beginPath();
        canvasContext.strokeStyle = "#facc15";
        canvasContext.lineWidth = 2;
        canvasContext.setLineDash([6, 3]);
        canvasContext.moveTo(points[0].x*w, points[0].y*h);

        for (let i = 1; i < points.length; i++) {
            canvasContext.lineTo(points[i].x*w, points[i].y*h)

        }

        if (points.length > 2) {
            canvasContext.lineTo(points[0].x*w, points[0].y*h) ///this will close the preview


        }
        canvasContext.stroke();



        //drawing the vertex dots
        for (const p of points) {
            canvasContext.beginPath();
            canvasContext.fillStyle = "#facc15";
            canvasContext.arc(p.x*w, p.y*h, 5, 0, Math.PI*2); //this needs some checking
            canvasContext.fill();


        }

        //highlight the first point, so that the user knows to end the polygon by coming to this point
        canvasContext.beginPath();
        canvasContext.strokeStyle = "#fff";
        canvasContext.lineWidth = 1;
        canvasContext.arc(points[0].x*w, points[0].y*h, 8, 0, Math.PI*2);
        canvasContext.stroke();

    }, [points, videoRef]);


    useEffect(() => { draw() }, [draw]);

    
    const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {

        const canvas = canvasRef.current;
        if (!canvas) return;


        const rect = canvas.getBoundingClientRect(); //so we can get the canvas position on the page
        const normalizedX = (e.clientX - rect.left) / rect.width;
        const normalizedY = (e.clientY - rect.top) / rect.height;


        ///closing polygon if we click nearthe first point
        if (points.length >= 3) {

            const distanceX = normalizedX - points[0].x;
            const distanceY = normalizedY - points[0].y;

            //314's euclidean distance :(
            if (Math.sqrt(distanceX * distanceX  +  distanceY * distanceY) < 0.03) {
                handleSave();
                return;
            }

        }


        setPoints(prev => [...prev, {
            x: normalizedX,
            y: normalizedY
        }]);

    }


    const handleSave = async() => {

        if (points.length < 3) return;
        setSaving(true);

        try {
            
            const polygon = points.map(p => [p.x, p.y]);
            await onSave(polygon, `Zone ${Date.now()}`);
            setPoints([]);

        }
        finally {

            setSaving(false);
        }

    }




    //rendering
    return (

        <div className="relative">
            <p className="text-xs text-muted-foreground mb-2">
                Click on the camera view to add zone vertices. Click near the first point to close and save.

            </p>

            <div className="relative">
                <video
                    ref={videoRef}
                    autoPlay playsInline muted
                    className="w-full rounded-md"
                />

                <canvas
                    ref={canvasRef}
                    className="absolute inset-0 w-full h-full cursor-crosshair"
                    onClick={handleClick}
                />


            </div>
            <div className="flex gap-2 mt-3">
                <Button
                    size="sm"
                    onClick={handleSave}
                    disabled={points.length < 3 || saving}
                >
                    {saving ? "Saving...": `Save zone (${points.length} pts)`}

                </Button>

                <Button size="sm"
                        variant="outline"
                        onClick={() => setPoints([])}>
                            Clear
                </Button>

                <Button size="sm"
                        variant="ghost"
                        onClick={onCancel}>
                            Cancel
                </Button>
            </div>
        </div>

    )

}
