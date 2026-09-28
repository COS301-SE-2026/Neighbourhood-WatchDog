"use client";

import { usePropertyContext } from "@/hooks/use-property-context";
import { DispatchRequestPopup } from "./shared/DispatchRequestPopup";

export default function OfficerDispatchPopup() {
  const { contexts, isLoading } = usePropertyContext();

  if (isLoading) return null;

  const officerContext = contexts.find(
    (context) =>
      context.role === "Security Officer" && context.neighbourhoodId !== null,
  );

  if (!officerContext) return null;

  return (
    <DispatchRequestPopup neighbourhoodId={officerContext.neighbourhoodId} />
  );
}
