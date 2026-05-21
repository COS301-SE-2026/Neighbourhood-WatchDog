"use client"

import { CreatePropertyDialog } from "@/components/create-property-dialogue";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { PropertyRes } from "@/lib/validators/property";

export default function Test() {
  const [open, setOpen] = useState(false);

  const handlePropertyAdded = (property: PropertyRes) => {
    console.log("Property created:", property)
    alert(`Property created!\n\nAddress: ${property.address}\nType: ${property.property_type}`);
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Create Property Dialog Test</h1>
      <Button onClick={() => setOpen(true)}>Open Create Property Dialog</Button>
      <CreatePropertyDialog
        open={open}
        onOpenChange={setOpen}
        onPropertyAdded={handlePropertyAdded}
      />
    </div>
  );
}