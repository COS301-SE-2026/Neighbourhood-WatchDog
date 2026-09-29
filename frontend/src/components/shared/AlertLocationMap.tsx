"use client";

import { useEffect } from "react";
import { divIcon } from "leaflet";
import {
    MapContainer,
    Marker,
    TileLayer,
    useMap,
} from "react-leaflet";

interface AlertLocationMapProps {
    readonly latitude: number;
    readonly longitude: number;
}

function RecenterMap({
    latitude,
    longitude,
}: AlertLocationMapProps) {
    const map = useMap();

    useEffect(() => {
        map.setView([latitude, longitude], 16);
    }, [latitude, longitude, map]);

    return null;
}

const ALERT_MAP_ICON = divIcon({
    className: "",
    iconSize: [40, 36],
    iconAnchor: [20, 33],
    tooltipAnchor: [0, -30],
    html: `
        <svg
            width="40"
            height="36"
            viewBox="0 0 40 36"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
        >
            <path
                d="M20 2 L38 34 H2 Z"
                fill="#facc15"
                stroke="#ef4444"
                stroke-width="3"
                stroke-linejoin="round"
            />
            <path
                d="M20 11 V23"
                stroke="#111827"
                stroke-width="3.5"
                stroke-linecap="round"
            />
            <circle
                cx="20"
                cy="28"
                r="2"
                fill="#111827"
            />
        </svg>
    `,
});

export function AlertLocationMap({
    latitude,
    longitude,
}: AlertLocationMapProps) {
    const position: [number, number] = [
        latitude,
        longitude,
    ];

    return (
        <div className="overflow-hidden rounded-lg border border-border">
            <MapContainer
                center={position}
                zoom={16}
                maxZoom={19}
                className="h-48 w-full"
                scrollWheelZoom={false}
                dragging={false}
                doubleClickZoom={false}
                touchZoom={false}
                boxZoom={false}
                keyboard={false}
                zoomControl={false}
                attributionControl={true}
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
                    icon={ALERT_MAP_ICON}
                    title="Alert location"
                />
            </MapContainer>
        </div>
    );
}