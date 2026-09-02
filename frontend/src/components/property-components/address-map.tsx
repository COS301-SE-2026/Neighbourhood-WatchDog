"use client";

import { useEffect } from "react";
import {
    CircleMarker,
    MapContainer,
    TileLayer,
    useMap,
} from "react-leaflet";

interface AddressMapProps {
    latitude: number;
    longitude: number;
}

function RecenterMap({
    latitude,
    longitude,
}: AddressMapProps) {
    const map = useMap();
    const position: [number, number] = [latitude, longitude];

    useEffect(() => {
        map.setView([latitude, longitude], 16);
    }, [latitude, longitude, map]);

    return null;
}

export function AddressMap({
    latitude,
    longitude,
}: AddressMapProps) {
    const position: [number, number] = [latitude, longitude];

    return (
        <div className="mt-4 overflow-hidden rounded-lg border border-white/10">
            <MapContainer
                center={position}
                zoom={16}
                scrollWheelZoom={false}
                className="h-56 w-full"
            >
                <RecenterMap
                    latitude={latitude}
                    longitude={longitude}
                />

                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO'
                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                />



                <CircleMarker
                    center={position}
                    radius={8}
                    pathOptions={{
                        color: "#10b981",
                        fillColor: "#10b981",
                        fillOpacity: 0.8,
                    }}
                />
            </MapContainer>
        </div>
    );
}
