"use client";

import {
  Building2,
  CheckCircle2,
  Home,
  LockKeyhole,
} from "lucide-react";

import { Button } from "@/components/ui/button";

const properties = [
  {
    id: "30000000-0000-0000-0000-000000000001",
    address: "12 Test Street, Hatfield, Pretoria",
    property_type: "PRIVATE",
    neighbourhood_id: null,
    neighbourhood_name: "",
  },
  {
    id: "30000000-0000-0000-0000-000000000002",
    address: "45 Main Road, Brooklyn, Pretoria",
    property_type: "PUBLIC",
    neighbourhood_id: "40000000-0000-0000-0000-000000000001",
    neighbourhood_name: "Greenstone Estate",
  },
];

function formatPropertyType(propertyType: string) {
  return propertyType === "PRIVATE"
    ? "Private property"
    : "Public property";
}

export default function NeighbourhoodPage() {
  const availableProperties = properties.filter(
    (property) => property.neighbourhood_id === null
  );

  return (
    <div className="w-full p-6 md:p-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 flex flex-col gap-4 border-b border-border pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="mb-2 text-sm font-medium text-primary">
              Neighbourhood management
            </p>

            <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-3xl">
              Set up a neighbourhood
            </h1>

            <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted-foreground">
              Choose a property to use as the starting point for your
              neighbourhood. Additional properties and residents can be added
              after setup.
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-primary" />
            <span>
              {availableProperties.length} propert
              {availableProperties.length === 1 ? "y" : "ies"} available
            </span>
          </div>
        </div>

        
      </div>
    </div>
  );
}