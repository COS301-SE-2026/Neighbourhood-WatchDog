"use client"

import { InfoCard } from "@/components/info-card";
import { ListCard } from "@/components/list-card";
import { AddCameraDialogBox } from "@/components/add-camera-dialogue";
import { useCameras } from "@/hooks/use-camera";
import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { getPropertyDetails } from "@/lib/api/property";
import { PropertyDetailedRes } from "@/lib/validators/property";
import { CreateNeighbourhoodDialog } from "@/components/create-neighbourhood-dialog";
import { NeighbourhoodRes } from "@/lib/validators/neighbourhood";

const PROPERTY_ID = "30000000-0000-0000-0000-000000000001" // TODO: Get from URL params or props

function PropertyPageContent(){
  const searchParams = useSearchParams()
  const propertyId = searchParams.get("id") || PROPERTY_ID

  const [neighbourhoodDialogOpen, setNeighbourhoodDialogOpen] = useState(false);
  const [cameraDialogOpen, setCameraDialogOpen] = useState(false)
  const { addCamera, deleteCamera } = useCameras(propertyId || PROPERTY_ID)
  const [propertyData, setPropertyData] = useState<PropertyDetailedRes | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() =>{
    if (!propertyId && !PROPERTY_ID){
      return;
    } 

    const fetchProperty = async () => {
      try {

        const propInfo = await getPropertyDetails(propertyId)
        setPropertyData(propInfo)

      } catch (error) {
        console.error("Failed to fetch property:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchProperty()
  }, [propertyId])

  if (loading) return <div className="p-6">Loading... </div>
  if (!propertyData) return <div className="p-6">Property not found </div>

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
          items={propertyData.users.map((u: { id: string; email: string; first_name?: string | null; last_name?: string | null }) => ({
            id: u.id,
            name: `${u.first_name || ''} ${u.last_name || ''}`.trim(),
          }))}
        onAdd={() => console.log("Add member")}
        onDelete={(id) => console.log("Delete", id)}
        />

      <InfoCard title="Neighbourhood">
        {propertyData.neighbourhood && (
          <>
            <div>Name: {propertyData.neighbourhood.name}</div>
            <div>Location: {propertyData.neighbourhood.location}</div>
          </>
        )}
        {!propertyData.neighbourhood && (
          <>
            <p className="text-sm text-body mb-4">No neighbourhood assigned</p>
            <button
              onClick={() => setNeighbourhoodDialogOpen(true)}
              className="px-4 py-2 bg-blue text-white rounded hover:bg-sky"
            >
              Create Neighbourhood
            </button>
            <CreateNeighbourhoodDialog
              open={neighbourhoodDialogOpen}
              onOpenChange={setNeighbourhoodDialogOpen}
              onNeighbourhoodAdded={(neighbourhood: NeighbourhoodRes) => {
                setPropertyData({ 
                  ...propertyData, 
                  neighbourhood: {
                    id: neighbourhood.id,
                    name: neighbourhood.name,
                    location: neighbourhood.location,
                    join_code: neighbourhood.join_code,
                    created_at: neighbourhood.created_at,
                  }
                });
                setNeighbourhoodDialogOpen(false);
              }}
            />
          </>
        )}
      </InfoCard>

      <ListCard

          title="Cameras"
          items={propertyData.cameras.map((c: { id: string; location: string }) => ({
            id: c.id,
            name: c.location,
          }))}
          onAdd={() => setCameraDialogOpen(true)}
          onDelete={deleteCamera}

        />
      </div>
      <AddCameraDialogBox

        open={cameraDialogOpen}
        onOpenChange={setCameraDialogOpen}
        onCameraAdded={addCamera}
        propertyId={propertyId || PROPERTY_ID} //TODO: change this mock
        
      />
    </>
  )
}

export default function PropertyPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading...</div>}>
      <PropertyPageContent />
    </Suspense>
  )
}