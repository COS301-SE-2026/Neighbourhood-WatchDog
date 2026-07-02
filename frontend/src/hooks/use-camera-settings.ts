"use client";
import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib/api/client";


export interface Zone {

    id: string
    camera_id: string
    name: string
    polygon: number[][]

}


export interface CameraSettings {

    camera_id: string
    confidence_threshold: number
    zones: Zone[]

}


export function useCameraSettings(cameraId: string) {

    const [settings, setSettings] = useState<CameraSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);


    //downloading the latest setting from the backend
    const fetchSettings = useCallback(async () => {

        try {
            
            const data = await apiCall<CameraSettings>(`/cameras/${cameraId}/settings`);
            setSettings(data);

        }
        catch (e) {

            setError(`Failed to load camera settings: \n${e}`);

        }
        finally {

            setLoading(false);

        }

    }, [cameraId])

    useEffect(() => { const load = async () => {
                        await fetchSettings() ;
                    };

                    void load();
                }, [fetchSettings]);


    const updateThreshold = useCallback(async (threshold: number) => {

        await apiCall(`/cameras/${cameraId}/settings`, {
            method: "PATCH",
            body: JSON.stringify({
                confidence_threshold: threshold
            })
        });

        setSettings(prev => prev ? {...prev, confidence_threshold: threshold} : prev);
    
    }, [cameraId]);



    const createZone = useCallback(async (polygon: number[][], name = "Zone") => {

        try{

            const zone = await apiCall<Zone>(`/cameras/${cameraId}/zones`, {
                method: "POST",
                body: JSON.stringify({
                    name,
                    polygon
                })
            });

            setSettings(prev => prev ? {...prev, zones: [...prev.zones, zone]} : prev);
        }
        catch (e: unknown) {
            const message = e instanceof Error ? e.message : JSON.stringify(e);
            console.error("Zone save failed: ", message);
            alert("Zone save error: " + message);
        }

    }, [cameraId]);



    const deleteZone = useCallback(async (zoneId: string) => {

        await apiCall(`/cameras/${cameraId}/zones/${zoneId}`, {
            method: "DELETE"
        });

        setSettings(prev => prev ? {...prev, zones: prev.zones.filter(z => z.id !== zoneId)} : prev);

    }, [cameraId]);




    return {
        settings, 
        loading, 
        error, 
        updateThreshold, 
        createZone, 
        deleteZone, 
        refetch: fetchSettings
        
    }



}