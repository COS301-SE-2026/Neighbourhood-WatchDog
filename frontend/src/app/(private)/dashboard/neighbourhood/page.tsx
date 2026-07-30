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
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-4 border-b border-border pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="mb-2 text-lg font-medium text-primary">
              Neighbourhood management
            </h1>

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

        <section className="rounded-2xl border border-border bg-card">
          <div className="flex flex-col gap-2 border-b border-border px-5 py-5 md:px-6">
            <h2 className="text-base font-semibold text-card-foreground">
              Choose a property
            </h2>

            <p className="text-sm text-muted-foreground">
              Properties already linked to a neighbourhood cannot be used
              again.
            </p>
          </div>

          <div className="divide-y divide-border">
            {properties.map((property) => {
              const isAvailable = property.neighbourhood_id === null;

              return (
                <div
                  key={property.id}
                  className="flex flex-col gap-4 px-5 py-5 md:flex-row md:items-center md:justify-between md:px-6"
                >
                  <div className="flex min-w-0 items-start gap-4">
                    <div
                      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                        isAvailable
                          ? "bg-primary/10 text-primary"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {property.property_type === "PRIVATE" ? (
                        <Home className="h-5 w-5" />
                      ) : (
                        <Building2 className="h-5 w-5" />
                      )}
                    </div>

                    <div className="min-w-0">
                      <p className="truncate font-medium text-card-foreground">
                        {property.address}
                      </p>

                      <p className="mt-1 text-sm text-muted-foreground">
                        {formatPropertyType(property.property_type)}
                      </p>
                    </div>
                  </div>

                  {isAvailable ? (
                    <Button
                      type="button"
                      className="w-full bg-primary text-primary-foreground hover:bg-primary/90 md:w-auto"
                    >
                      Use this property
                    </Button>
                  ) : (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground md:justify-end">
                      <LockKeyhole className="h-4 w-4 shrink-0" />
                      <span>
                        Linked to{" "}
                        <span className="font-medium text-foreground">
                          {property.neighbourhood_name}
                        </span>
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}