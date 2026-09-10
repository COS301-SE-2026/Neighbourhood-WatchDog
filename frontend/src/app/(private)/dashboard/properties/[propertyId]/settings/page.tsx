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
