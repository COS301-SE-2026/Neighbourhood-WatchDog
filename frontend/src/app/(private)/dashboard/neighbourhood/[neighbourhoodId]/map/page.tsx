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

  return (
    <main className="min-h-full bg-brand-void px-6 py-8 text-brand-frost md:px-8">
      <div className="w-full max-w-6xl">
        <header className="mb-6 flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="size-5 text-brand-threat" />

              <h1 className="text-2xl font-semibold tracking-tight">
                Critical alert map
              </h1>
            </div>

            <p className="mt-2 text-sm text-brand-ash">
              Monitor weapon and fall detections
              throughout your neighbourhood.
            </p>

            {lastUpdated && (
              <p className="mt-2 flex items-center gap-1.5 text-xs text-brand-ash">
                <Clock className="size-3.5" />
                Last updated{" "}
                {formatDateTime(lastUpdated)}
              </p>
            )}
          </div>

          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={loading}
            onClick={() => void refetch()}
            className="border-border bg-transparent text-brand-green hover:bg-brand-slate hover:text-brand-frost"
          >
            <RefreshCw
              className={`mr-1.5 size-3.5 ${
                loading ? "animate-spin" : ""
              }`}
            />
            Refresh
          </Button>
        </header>

        {error && (
          <div
            role="alert"
            className="mb-5 flex items-start gap-3 rounded-lg border border-brand-threat/30 bg-brand-threat/10 px-4 py-3"
          >
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-brand-threat" />

            <div>
              <p className="text-sm font-medium text-brand-threat">
                Unable to refresh map
              </p>

              <p className="mt-1 text-xs text-brand-ash">
                {mappedAlerts.length > 0
                  ? "Showing the most recently loaded alerts."
                  : error}
              </p>
            </div>
          </div>
        )}

        <section className="mb-5 grid gap-3 sm:grid-cols-3">
          <SummaryCard
            label="Mapped alerts"
            value={mappedAlerts.length}
            colour="text-brand-frost"
          />

          <SummaryCard
            label="Open alerts"
            value={
              mappedAlerts.filter(
                (alert) =>
                  alert.status === "OPEN",
              ).length
            }
            colour="text-brand-threat"
          />

          <SummaryCard
            label="Missing coordinates"
            value={unlocatedAlerts.length}
            colour="text-brand-caution"
          />
        </section>

        {loading && mappedAlerts.length === 0 ? (
          <MapLoadingState />
        ) : (
          <CriticalAlertsMap
            alerts={mappedAlerts}
          />
        )}

        <UnlocatedAlerts
          alerts={unlocatedAlerts}
        />
      </div>
    </main>
  );

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
