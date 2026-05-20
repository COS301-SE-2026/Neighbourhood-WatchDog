"use client"

import { InfoCard } from "@/components/info-card";
import { ListCard } from "@/components/list-card";
import { DialogBox } from "@/components/add-camera-dialogue";
import { useState } from "react";


export default function PropertyPage(){
  const [cameraDialogOpen, setCameraDialogOpen] = useState(false)

  return (
    <>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
      <InfoCard title="Property Name">
        <div>1234 Property Road</div>
        <div>Suburb</div>
        <div>Property Type</div>
      </InfoCard>

      <ListCard
        title="Property Members"
        items={[
        { id: "1", name: "John" },
        { id: "2", name: "Mary" },
        { id: "3", name: "Name" },
        { id: "4", name: "T" },
        ]}
        onAdd={() => console.log("Add member")}
        onDelete={(id) => console.log("Delete", id)}
        />

      <InfoCard title="Neighborhood">
        <div>Name: neighborhood name</div>
        <div>Location: location name</div>
      </InfoCard>

      <ListCard
        title="Cameras"
        items={[{ id: "1", name: "Backyard" }]}
        onAdd={() => setCameraDialogOpen(true)}
        onDelete={(id) => console.log("Delete", id)}
      />
    </div>
    <DialogBox open={cameraDialogOpen} onOpenChange={setCameraDialogOpen} />
    </>
  )
}