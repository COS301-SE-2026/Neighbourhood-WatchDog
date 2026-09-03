
"use client";

import { useEffect } from "react";
import { CircleMarker, MapContainer, TileLayer, useMap } from "react-leaflet";

interface AlertLocationMapProps {
  readonly latitude: number;
  readonly longitude: number;

}

function RecenterMap({ latitude, longitude }: AlertLocationMapProps) {

  const map = useMap();

  useEffect(() => {
    map.setView([latitude, longitude], 16);

  }, [latitude, longitude, map]);

  return null;


}

export function AlertLocationMap({ latitude, longitude }: AlertLocationMapProps) {
    
  const position: [number, number] = [latitude, longitude];

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <MapContainer
        center={position}
        zoom={16}
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
        <RecenterMap latitude={latitude} longitude={longitude} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        <CircleMarker
          center={position}
          radius={8}
          pathOptions={{
            color: "var(--color-green)",
            fillColor: "var(--color-green)",
            fillOpacity: 0.85,
          }}
        />
      </MapContainer>
    </div>
  );
}
