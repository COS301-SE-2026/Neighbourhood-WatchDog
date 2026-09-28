"use client";

import { usePropertyContext } from "@/hooks/use-property-context";
import { DispatchRequestPopup } from "./shared/DispatchRequestPopup";

export default function OfficerDispatchPopup() {
  const { contexts, isLoading } = usePropertyContext();

  if (isLoading) return null;

  const isSecurityOfficer = contexts.some(
    (context) => context.role === "Security Officer",
  );

  return isSecurityOfficer ? <DispatchRequestPopup /> : null;
}
