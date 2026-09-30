"use client";

import { usePropertyContext } from "@/hooks/use-property-context";
import { NoCandidatePopup } from "./shared/NoCandidatePopup";

export default function AdminDispatchPopup() {
  const { activeContext, isLoading } = usePropertyContext();

  if (isLoading) return null;

  if (
    isLoading ||
    activeContext?.role !== "Neighbourhood Admin" ||
    !activeContext.neighbourhoodId
  ) {
    return null;
  }

  return <NoCandidatePopup neighbourhoodId={activeContext.neighbourhoodId} />;
}
