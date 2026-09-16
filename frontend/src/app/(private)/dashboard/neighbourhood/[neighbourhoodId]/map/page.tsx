"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  Clock,
  MapPinOff,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useCriticalAlerts } from "@/hooks/use-critical-alerts";
import { useUserContext } from "@/hooks/use-user-context";
import type {
  UnlocatedCriticalAlertItem,
} from "@/lib/validators/alert";

const CriticalAlertsMap = dynamic(
  () =>
    import("./CriticalAlertsMap").then(
      (module) => module.CriticalAlertsMap,
    ),
  {
    ssr: false,
    loading: () => (
      <MapLoadingState />
    ),
  },
);

function formatDateTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-ZA", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function detectionLabel(
  type: UnlocatedCriticalAlertItem["detection_type"],
): string {
  return type === "WEAPON_DETECTED"
    ? "Weapon detected"
    : "Fall detected";
}

function MapLoadingState() {
  return (
    <div className="flex h-[34rem] items-center justify-center rounded-lg border border-border bg-brand-depth">
      <RefreshCw className="size-5 animate-spin text-brand-green" />
    </div>
  );
}

export default function NeighbourhoodAlertMapPage() {
  const { neighbourhoodId } = useParams<{
    neighbourhoodId: string;
  }>();

  const {
    data: userContext,
    isLoading: userContextLoading,
  } = useUserContext();

  const neighbourhoodRole =
    userContext?.properties.find(
      (property) =>
        property.neighbourhood?.id ===
        neighbourhoodId,
    )?.neighbourhood?.role ?? null;

  const isSecurityOfficer =
    neighbourhoodRole === "SECURITY_OFFICER";

  const {
    mappedAlerts,
    unlocatedAlerts,
    lastUpdated,
    loading,
    error,
    refetch,
  } = useCriticalAlerts(
    isSecurityOfficer ? neighbourhoodId : "",
  );

  if (userContextLoading) {
    return (
      <main className="min-h-full bg-brand-void px-6 py-8">
        <MapLoadingState />
      </main>
    );
  }

  if (!isSecurityOfficer) {
    return (
      <main className="min-h-full bg-brand-void px-6 py-8 text-brand-frost">
        <div className="mx-auto max-w-6xl">
          <Card className="border-border bg-brand-depth p-6">
            <h1 className="text-lg font-semibold">
              Access denied
            </h1>

            <p className="mt-2 text-sm text-brand-ash">
              The critical-alert map is available only
              to security officers in this neighbourhood.
            </p>
          </Card>
        </div>
      </main>
    );
  }
}

function SummaryCard({
  label,
  value,
  colour,
}: {
  readonly label: string;
  readonly value: number;
  readonly colour: string;
}) {
  return (
    <Card className="border-border bg-brand-depth p-4">
      <p className="text-xs uppercase tracking-wide text-brand-ash">
        {label}
      </p>

      <p className={`mt-2 text-2xl font-semibold ${colour}`}>
        {value}
      </p>
    </Card>
  );
}

function UnlocatedAlerts({
  alerts,
}: {
  readonly alerts: UnlocatedCriticalAlertItem[];
}) {
  return (
    <Card className="mt-6 overflow-hidden border-border bg-brand-depth">
      <div className="flex items-start gap-3 border-b border-border px-5 py-4">
        <MapPinOff className="mt-0.5 size-4 text-brand-caution" />

        <div>
          <h2 className="text-sm font-semibold">
            Alerts missing coordinates
          </h2>

          <p className="mt-1 text-xs text-brand-ash">
            These alerts cannot be placed on the map.
          </p>
        </div>
      </div>

      {alerts.length === 0 ? (
        <p className="px-5 py-10 text-center text-sm text-brand-ash">
          All critical alerts have valid coordinates.
        </p>
      ) : (
        <div className="divide-y divide-border">
          {alerts.map((alert) => (
            <article
              key={alert.id}
              className="flex flex-col gap-2 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="text-sm font-medium">
                  {detectionLabel(
                    alert.detection_type,
                  )}
                </p>

                <p className="mt-1 text-xs text-brand-ash">
                  {alert.property_address}
                </p>

                <p className="mt-1 text-xs text-brand-ash/70">
                  {alert.camera_name} ·{" "}
                  {formatDateTime(
                    alert.created_at,
                  )}
                </p>
              </div>

              <span className="w-fit rounded-full border border-border bg-brand-slate px-2.5 py-1 text-xs text-brand-ash">
                {alert.status}
              </span>
            </article>
          ))}
        </div>
      )}
    </Card>
  );
}
