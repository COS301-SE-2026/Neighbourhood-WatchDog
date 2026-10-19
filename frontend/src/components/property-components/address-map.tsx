"use client";

import { useEffect } from "react";
import {
    MapContainer,
    Marker,
    TileLayer,
    useMap,
} from "react-leaflet";

import {
    PROPERTY_MAP_ICON,
} from "@/components/shared/property-map-icon";

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
        <div className="mt-4 overflow-hidden rounded-lg border border-border">
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
                    maxZoom={19}
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                />



                <Marker
                    position={position}
                    icon={PROPERTY_MAP_ICON}
                />
            </MapContainer>
        </div>
    );
}
