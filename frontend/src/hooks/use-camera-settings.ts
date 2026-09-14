"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import { apiCall } from "@/lib/api/client";
import { clear } from "console";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ZONE_APPLY_SETTLE_MS = 5000;

export type ZoneMutation = "adding" | "removing" | null;


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
    const isValidUUID = UUID_REGEX.test(cameraId);

    const [settings, setSettings] = useState<CameraSettings | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [refetchToken, setRefetchToken] = useState(0);

    const [zoneMutation, setZoneMutation] = useState<ZoneMutation>(null);
    const settleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const [loadedFor, setLoadedFor] = useState<string | null>(null);


    if (cameraId !== loadedFor && settings !== null) {
        setSettings(null);
    }
    if (cameraId !== loadedFor && error !== null) {
        setError(null);
    }


    const loading = isValidUUID && loadedFor !== cameraId;

    useEffect(() => {
        if (!isValidUUID) return;

        let ignore = false;

        apiCall<CameraSettings>(`/cameras/${cameraId}/settings`)
            .then(data => {
                if (ignore) return;
                setSettings(data);
                setLoadedFor(cameraId);
            })
            .catch(e => {
                if (ignore) return;
                setError(`Failed to load camera settings: \n${e}`);
                setLoadedFor(cameraId);
            });

        return () => {
            ignore = true;
        };
    }, [cameraId, isValidUUID, refetchToken]);

    useEffect(() => {
        return () => {
            if (settleTimerRef.current !== null) {
                clearTimeout(settleTimerRef.current);
            }
        }
    }, []);

    const refetch = useCallback(() => {
        setRefetchToken(t => t + 1);
    }, []);

    const updateThreshold = useCallback(async (threshold: number) => {
        if (!isValidUUID) return;
        await apiCall(`/cameras/${cameraId}/settings`, {
            method: "PATCH",
            body: { confidence_threshold: threshold }
        });
        setSettings(prev => prev ? { ...prev, confidence_threshold: threshold } : prev);
    }, [cameraId, isValidUUID]);


    const beginZoneMutation = useCallback((mutation: Exclude<ZoneMutation, null>) => {
        if (settleTimerRef.current !== null) {
            clearTimeout(settleTimerRef.current);
            settleTimerRef.current = null;
        }

        setZoneMutation(mutation);
    }, []);

    const keepZoneMutationVisibileBreifly = useCallback(() => {
        if (settleTimerRef.current !== null){
            clearTimeout(settleTimerRef.current);
        }

        settleTimerRef.current = setTimeout(() => {
            settleTimerRef.current = null;
            setZoneMutation(null);

        }, ZONE_APPLY_SETTLE_MS);
    }, []);

    const failZoneMutation = useCallback(() => {
        if (settleTimerRef.current !== null) {
            clearTimeout(settleTimerRef.current);
            settleTimerRef.current = null;
        }

        setZoneMutation(null);
    }, []);
    

    const createZone = useCallback(async (polygon: number[][], name = "Zone") => {
        if (!isValidUUID) return;

        beginZoneMutation("adding");

        try {
            const zone = await apiCall<Zone>(`/cameras/${cameraId}/zones`, {
                method: "POST",
                body: { name, polygon }
            });
            setSettings(prev => prev ? { ...prev, zones: [...prev.zones, zone] } : prev);

            keepZoneMutationVisibileBreifly();
        } catch (e: unknown) {
            const message = e instanceof Error ? e.message : JSON.stringify(e);
            console.error("Zone save failed: ", message);
            alert("Zone save error: " + message);
        }
    }, [beginZoneMutation, cameraId, failZoneMutation, isValidUUID, keepZoneMutationVisibileBreifly]);

    const deleteZone = useCallback(async (zoneId: string) => {
        if (!isValidUUID) return;

        beginZoneMutation("adding");

        try {
            await apiCall(`/cameras/${cameraId}/zones/${zoneId}`, { method: "DELETE" });
            setSettings(prev => prev ? { ...prev, zones: prev.zones.filter(z => z.id !== zoneId) } : prev);

            keepZoneMutationVisibileBreifly();
        }
        catch (e: unknown) {
            failZoneMutation();

            const message = e instanceof Error ? e.message : JSON.stringify(e);
            console.error("Zone delete failed: ", message);

            alert("Zone delete error: " + message);
        }
    }, [beginZoneMutation, cameraId, failZoneMutation, isValidUUID, keepZoneMutationVisibileBreifly]);

    return { settings, loading, error, zoneMutation, updateThreshold, createZone, deleteZone, refetch };
}