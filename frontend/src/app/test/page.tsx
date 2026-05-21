"use client"

import { CreateNeighbourhoodDialog } from "@/components/create-neighbourhood-dialog";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { NeighbourhoodRes } from "@/lib/validators/neighbourhood";

export default function Test() {
  const [open, setOpen] = useState(false);
  const [createdNeighbourhood, setCreatedNeighbourhood] = useState<NeighbourhoodRes | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleNeighbourhoodAdded = (neighbourhood: NeighbourhoodRes) => {
    console.log("Neighbourhood created:", neighbourhood);
    setError(null);
    setCreatedNeighbourhood(neighbourhood);
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Create Neighbourhood Dialog Test</h1>
      <Button onClick={() => setOpen(true)}>Open Create Neighbourhood Dialog</Button>
      {error && (
        <div className="mt-4 p-4 border border-red-300 bg-red-50 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}
      <CreateNeighbourhoodDialog
        open={open}
        onOpenChange={setOpen}
        onNeighbourhoodAdded={handleNeighbourhoodAdded}
      />

      {createdNeighbourhood && (
        <div className="mt-8 p-4 border border-green-300 bg-green-50 rounded-lg">
          <h2 className="text-lg font-bold mb-4">Created Neighbourhood</h2>
          <pre className="bg-white p-4 rounded border overflow-auto text-sm">
            {JSON.stringify(createdNeighbourhood, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}