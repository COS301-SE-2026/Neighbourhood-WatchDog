"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2, LogOut } from "lucide-react";
import { toast } from "sonner";

import { leaveNeighbourhood } from "@/lib/api/neighbourhood";
import { useUserContext } from "@/hooks/use-user-context";



export default function PropertySettingsPage() {
  const { propertyId } = useParams<{ propertyId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: userContext, isLoading } = useUserContext();

  const [isLeaving, setIsLeaving] = useState(false);

  const property = userContext?.properties.find(
    (item) => item.id === propertyId,
  );

  async function handleLeaveNeighbourhood() {
    if (
      !property?.is_admin ||
      !property.neighbourhood
    ) {
      return;
    }

    setIsLeaving(true);

    try {
      await leaveNeighbourhood({
        neighbourhoodId: property.neighbourhood.id,
        propertyId: property.id,
      });

      await queryClient.invalidateQueries({
        queryKey: ["userContext"],
      });

      toast.success("Property left the neighbourhood");

      router.replace(
        `/dashboard/properties/${property.id}/cameras`,
      );
    } catch (error: unknown) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to leave neighbourhood",
      );
    } finally {
      setIsLeaving(false);
    }
  }


  if (isLoading) {
    return (
      <main className="flex min-h-full items-center justify-center">
        <Loader2 className="size-5 animate-spin text-primary" />
      </main>
    );
  }

  if (!property) {
    return (
      <main className="p-8">
        <p className="text-destructive">Property not found.</p>
      </main>
    );
  }
}
