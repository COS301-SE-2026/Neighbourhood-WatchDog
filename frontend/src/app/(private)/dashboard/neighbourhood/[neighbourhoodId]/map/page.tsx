"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  Clock,
  MapPinOff,
  WifiOff,
  RefreshCw,
  ShieldAlert,
  Users,
  ChevronDown
} from "lucide-react";
import Link from "next/link";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useCriticalAlerts } from "@/hooks/use-critical-alerts";
import { useAlertPropertyRoute } from "@/hooks/use-alert-property-route";
import { useOfficerMapLocationTracking } from "@/hooks/use-officer-map-location-tracking";
import { useUserContext } from "@/hooks/use-user-context";
import { usePropertyResidentContext } from "@/hooks/use-property-resident-context";
import type { PropertyAlertGroup } from "./CriticalAlertsMap";
import type {
  CriticalAlertMapItem,
  AlertRouteData,
  CriticalAlertStatus,
  UnlocatedCriticalAlertItem,
} from "@/lib/validators/alert";
import { useEffect, useState } from "react";
import {AlertDetailSheet, type Alert} from "@/components/shared/AlertCard";
import { acknowledgeAlert } from "@/lib/api/alert";
import {
  MapModeTabs,
  type MapMode,
} from "./MapModeTabs";

import {
  MapLayerControls,
  type MapLayerKey,
  type MapLayerState,
} from "./MapLayerControls";

function statusLabel(
  status: CriticalAlertStatus,
): string {
  switch (status) {
    case "OPEN":
      return "Open";
    case "ACKNOWLEDGED":
      return "Acknowledged";
    case "CONFIRMED":
      return "Confirmed";
    case "DISMISSED":
      return "Dismissed";
    case "RESOLVED":
      return "Resolved";
  }
}


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

function connectionStatusLabel(
  isOnline: boolean,
  wsConnected: boolean,
): string {
  if (!isOnline) {
    return "Offline";
  }

  return wsConnected
    ? "Live updates connected"
    : "Connecting to live updates…";
}


function MapLoadingState() {
  return (
    <div className="flex h-[34rem] items-center justify-center rounded-lg border border-border bg-brand-depth">
      <RefreshCw className="size-5 animate-spin text-brand-green" />
    </div>
  );
}

function toAlertDetailModel(alert: CriticalAlertMapItem): Alert {
  const status: Alert["status"] =
    alert.status === "OPEN" ? "NEW" : alert.status;

  return {
    id: alert.id,
    camera_id: alert.camera_id,
    frame_timestamp: alert.created_at,
    detection_type: alert.detection_type,
    confidence_score: alert.confidence_score ?? undefined,
    thumbnail_url: alert.thumbnail_url,
    status,
    resolved_at: alert.resolved_at ?? undefined,
    created_at: alert.created_at,
    property_address: alert.property_address,
    property_latitude: alert.latitude,
    property_longitude: alert.longitude,
  };
}

function createGoogleMapsUrl(
  route: AlertRouteData,
): string {
  const params = new URLSearchParams({
    api: "1",
    origin:
      `${route.officer_latitude},` +
      `${route.officer_longitude}`,
    destination:
      `${route.property_latitude},` +
      `${route.property_longitude}`,
    travelmode: "driving",
  });

  return (
    "https://www.google.com/maps/dir/?" +
    params.toString()
  );
}


function RouteSummary({
  route,
  loading,
  error,
}: {
  readonly route: AlertRouteData | null;
  readonly loading: boolean;
  readonly error: string | null;
}) {
  if (loading) {
    return (
      <div className="mt-5 rounded-lg border border-border bg-brand-abyss p-4 text-sm text-brand-ash">
        Calculating route…
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-5 rounded-lg border border-brand-caution/30 bg-brand-caution/10 p-4">
        <p className="text-sm font-medium text-brand-caution">
          Route unavailable
        </p>

        <p className="mt-1 text-xs text-brand-ash">
          {error}
        </p>
      </div>
    );
  }

  if (!route) {
    return null;
  }

  const displayedDistance =
    route.route_distance_metres ??
    route.distance_metres;

  const distanceKilometres =
    displayedDistance / 1000;

  const etaMinutes =
    route.eta_seconds === null
      ? null
      : Math.max(
          1,
          Math.ceil(route.eta_seconds / 60),
        );

  const googleMapsUrl = createGoogleMapsUrl(route);

  return (
    <div className="mt-5 rounded-lg border border-border bg-brand-abyss p-4">
      <p className="text-xs uppercase tracking-wide text-brand-ash">
        Route to property
      </p>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-brand-ash">
            Distance
          </p>

          <p className="mt-1 text-lg font-semibold text-brand-frost">
            {distanceKilometres.toFixed(1)} km
          </p>
        </div>

        <div>
          <p className="text-xs text-brand-ash">
            ETA
          </p>

          <p className="mt-1 text-lg font-semibold text-brand-frost">
            {etaMinutes === null
              ? "Unavailable"
              : `${etaMinutes} min`}
          </p>
        </div>
      </div>

      {route.routing_error && (
        <p className="mt-3 text-xs text-brand-caution">
          {route.routing_error}
        </p>
      )}

      <a
        href={googleMapsUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-4 inline-flex w-full items-center justify-center rounded-md bg-brand-green px-4 py-2 text-sm font-semibold text-brand-void transition-colors hover:bg-brand-green/90"
      >
        Open in Google Maps
      </a>
    </div>
  );
}


function PropertyAlertsSheet({
  property,
  open,
  onClose,
  onSelectAlert,
  canShowRoute,
  onShowRoute,
}: {
  readonly property: PropertyAlertGroup | null;
  readonly open: boolean;
  readonly onClose: () => void;
  readonly canShowRoute: boolean;
  readonly onShowRoute: (
    propertyId: string,
  ) => void;
  readonly onSelectAlert: (
    alert: CriticalAlertMapItem,
  ) => void;
}) {
  const {
    data: residentContext,
    loading: residentsLoading,
    error: residentsError,
    retry: retryResidents,
  } = usePropertyResidentContext(
    property?.propertyId ?? null,
  );

  const [residentsExpanded, setResidentsExpanded] =
    useState(true);

  if (!property) {
    return null;
  }

  const visibleAlerts =
    property.alerts.slice(0, 20);

  return (
    <Sheet
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) {
          onClose();
        }
      }}
    >
      <SheetContent className="z-[1001] w-full overflow-y-auto border-border bg-brand-depth text-brand-frost sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="text-brand-frost">
            {property.propertyAddress}
          </SheetTitle>

          <SheetDescription className="text-brand-ash">
            {property.alerts.length} critical{" "}
            {property.alerts.length === 1
              ? "alert"
              : "alerts"}
          </SheetDescription>
        </SheetHeader>
        <section className="mt-6 rounded-lg border border-border bg-brand-abyss p-4">
          <button
            type="button"
            className="flex w-full items-start justify-between gap-3 text-left"
            onClick={() =>
              setResidentsExpanded((expanded) => !expanded)
            }
            aria-expanded={residentsExpanded}
            aria-controls="property-residents-content"
          >
            <span className="flex items-start gap-3">
              <Users className="mt-0.5 size-4 text-brand-green" />

              <span>
                <span className="block text-sm font-semibold text-brand-frost">
                  People at this property
                </span>

                <span className="mt-1 block text-xs text-brand-ash">
                  {residentsLoading
                    ? "Loading resident information..."
                    : residentsError
                      ? "Resident information unavailable"
                      : `${residentContext?.residents.length ?? 0} linked ${
                          residentContext?.residents.length === 1
                            ? "person"
                            : "people"
                        }`}
                </span>
              </span>
            </span>

            <ChevronDown
              className={`mt-0.5 size-4 shrink-0 text-brand-ash transition-transform ${
                residentsExpanded ? "rotate-180" : ""
              }`}
              aria-hidden="true"
            />
          </button>

          {residentsExpanded && (
            <div
              id="property-residents-content"
              className="mt-4"
            >
              {residentsLoading && (
                <div className="space-y-2">
                  <div className="h-10 animate-pulse rounded-md bg-brand-slate" />
                  <div className="h-10 animate-pulse rounded-md bg-brand-slate" />
                </div>
              )}

              {!residentsLoading && residentsError && (
                <div>
                  <p className="text-xs text-brand-caution">
                    {residentsError}
                  </p>

                  <button
                    type="button"
                    onClick={retryResidents}
                    className="mt-2 text-xs font-semibold text-brand-green hover:underline"
                  >
                    Try again
                  </button>
                </div>
              )}

              {!residentsLoading &&
                !residentsError &&
                residentContext?.residents.length === 0 && (
                  <p className="text-xs text-brand-ash">
                    No people are currently linked to this property.
                  </p>
                )}

              {!residentsLoading &&
                !residentsError &&
                residentContext &&
                residentContext.residents.length > 0 && (
                  <ul className="space-y-2">
                    {residentContext.residents.map((resident) => {
                      const fullName = [
                        resident.first_name,
                        resident.last_name,
                      ]
                        .filter(Boolean)
                        .join(" ");

                      return (
                        <li
                          key={resident.user_id}
                          className="rounded-md border border-border px-3 py-2"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-sm text-brand-frost">
                              {fullName || resident.email}
                            </p>

                            {resident.is_admin && (
                              <span className="shrink-0 rounded-full border border-brand-green/40 px-2 py-0.5 text-[10px] text-brand-green">
                                Property admin
                              </span>
                            )}
                          </div>

                          {fullName && (
                            <p className="mt-1 truncate text-xs text-brand-ash">
                              {resident.email}
                            </p>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
            </div>
          )}
        </section>

        {canShowRoute && (
          <Button
            type="button"
            className="mt-5 w-full bg-brand-green text-brand-void hover:bg-brand-green/90"
            onClick={() =>
              onShowRoute(property.propertyId)
            }
          >
            Show route
          </Button>
        )}


        <div className="mt-6 space-y-3">
          {visibleAlerts.map((alert) => (
            <article
              key={alert.id}
              className="rounded-lg border border-border bg-brand-abyss p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-semibold">
                  {detectionLabel(
                    alert.detection_type,
                  )}
                </p>

                <span className="rounded-full border border-border px-2 py-0.5 text-xs text-brand-ash">
                  {statusLabel(alert.status)}
                </span>
              </div>

              <p className="mt-3 text-xs text-brand-ash">
                Camera: {alert.camera_name}
              </p>

              <p className="mt-1 text-xs text-brand-ash">
                {formatDateTime(
                  alert.created_at,
                )}
              </p>

              <button
                  type="button"
                  onClick={() => onSelectAlert(alert)}
                  className="mt-3 inline-block text-xs font-semibold text-brand-green hover:underline"
                >
                  View alert
                </button>
            </article>
          ))}
        </div>

        {property.alerts.length > 20 && (
          <div className="mt-5 border-t border-border pt-4">
            <Link
              href={
                `/dashboard/neighbourhood/` +
                `${property.alerts[0].neighbourhood_id}/alerts`
              }
              className="text-sm font-semibold text-brand-green hover:underline"
            >
              View all {property.alerts.length} alerts
            </Link>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}


export default function NeighbourhoodAlertMapPage() {
  const [mapMode, setMapMode] =
    useState<MapMode>("neighbourhood");

  const [layerState, setLayerState] =
    useState<MapLayerState>({
      properties: true,
      heatmap: false,
      contours: false,
      liveAlerts: true,
      routes: false,
    });

  const [
    selectedProperty,
    setSelectedProperty,
  ] = useState<PropertyAlertGroup | null>(null);

  function handleSelectProperty(property: PropertyAlertGroup) {
    setSelectedAlert(null);
    setSelectedProperty(property);
  }

  async function handleAcknowledgeSelectedAlert(alertId: string) {
    setAcknowledgingAlert(true);

    try {
      await acknowledgeAlert(alertId);
      setSelectedAlert(null);
      await refetch();
    } catch (error) {
      console.error("Failed to acknowledge critical alert:", error);
    } finally {
      setAcknowledgingAlert(false);
    }
  }
  const [
    selectedAlert,
    setSelectedAlert,
  ] = useState<CriticalAlertMapItem | null>(null);

  const [acknowledgingAlert, setAcknowledgingAlert] =
    useState(false);
  const [routePropertyId, setRoutePropertyId] = useState<string | null>(null);

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

  const canViewSecurityMap =
    neighbourhoodRole === "SECURITY_OFFICER" ||
    neighbourhoodRole === "NEIGHBOURHOOD_ADMIN";

  const canAccessNeighbourhoodMap =
    neighbourhoodRole !== null;

  const isSecurityOfficer =
    neighbourhoodRole === "SECURITY_OFFICER";

  const showSecurityContent =
    mapMode === "security" &&
    canViewSecurityMap;
  
  function handleToggleLayer(layer: MapLayerKey) {
    if (
      layer === "liveAlerts" &&
      layerState.liveAlerts
    ) {
      setSelectedAlert(null);
      setSelectedProperty(null);
    }

    if (
      layer === "routes" &&
      layerState.routes
    ) {
      setRoutePropertyId(null);
    }

    setLayerState((current) => ({
      ...current,
      [layer]: !current[layer],
    }));
  }
  useEffect(() => {
    if (!canViewSecurityMap && mapMode === "security") {
      setMapMode("neighbourhood");
    }
  }, [canViewSecurityMap, mapMode]);

  useEffect(() => {
    if (mapMode !== "security") {
      setSelectedAlert(null);
      setSelectedProperty(null);
      setRoutePropertyId(null);
    }
  }, [mapMode]);

  useOfficerMapLocationTracking(
    neighbourhoodId,
    isSecurityOfficer && mapMode === "security",
  );



  const {
    mappedAlerts,
    unlocatedAlerts,
    lastUpdated,
    loading,
    error,
    refetch,
    isOnline,
    wsConnected,
    isStale,
    usingCachedData,
  } = useCriticalAlerts(
    showSecurityContent ? neighbourhoodId : "",
  );

  const currentSelectedProperty =
  selectedProperty
    ? {
        ...selectedProperty,
        alerts: mappedAlerts
          .filter(
            (alert) =>
              alert.property_id ===
              selectedProperty.propertyId,
          )
          .sort(
            (first, second) =>
              new Date(second.created_at).getTime() -
              new Date(first.created_at).getTime(),
          ),
      }
    : null;

  const {
    route,
    routeError,
    routeLoading,
  } = useAlertPropertyRoute(
    routePropertyId,
    isSecurityOfficer
  );



  if (userContextLoading) {
    return (
      <main className="min-h-full bg-brand-void px-6 py-8">
        <MapLoadingState />
      </main>
    );
  }

  if (!canAccessNeighbourhoodMap) {
    return (
      <main className="min-h-full bg-brand-void px-6 py-8 text-brand-frost">
        <div className="mx-auto max-w-6xl">
          <Card className="border-border bg-brand-depth p-6">
            <h1 className="text-lg font-semibold">
              Access denied
            </h1>

            <p className="mt-2 text-sm text-brand-ash">
              You must be a member of this neighbourhood to view its map.
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

            <p className="mt-1 text-xs text-brand-ash">
                {connectionStatusLabel(
                  isOnline,
                  wsConnected,
                )}
              </p>
          </div>

          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={loading || !isOnline}
            onClick={() => void refetch()}
            className="border-border bg-transparent text-brand-green hover:bg-brand-slate hover:text-brand-frost"
          >
            <RefreshCw
              className={`mr-1.5 size-3.5 ${
                loading ? "animate-spin" : ""
              }`}
            />
            {isOnline ? "Refresh" : "Offline"}
          </Button>
        </header>
        <section className="mb-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <MapModeTabs
              mode={mapMode}
              securityAvailable={canViewSecurityMap}
              onChange={setMapMode}
            />

            {mapMode === "security" && (
              <p className="text-xs text-brand-ash">
                Operational security view
              </p>
            )}
          </div>

          <MapLayerControls
            layers={layerState}
            showSecurityLayers={showSecurityContent}
            canViewRoutes={isSecurityOfficer}
            onToggle={handleToggleLayer}
          />
        </section>
        {isStale && (
          <output
            className="mb-5 flex items-start gap-3 rounded-lg border border-brand-caution/30 bg-brand-caution/10 px-4 py-3"
          >
            <WifiOff className="mt-0.5 size-4 shrink-0 text-brand-caution" />

            <div>
              <p className="text-sm font-medium text-brand-caution">
                {!isOnline
                  ? "You are offline"
                  : "Live updates disconnected"}
              </p>

              <p className="mt-1 text-xs text-brand-ash">
                {usingCachedData
                  ? "Showing the last saved alert-map state. It may be out of date."
                  : "The latest loaded alerts remain visible while live updates reconnect."}
              </p>

              {lastUpdated && (
                <p className="mt-1 text-xs text-brand-ash/70">
                  Data last updated{" "}
                  {formatDateTime(lastUpdated)}
                </p>
              )}

              <p className="mt-1 text-xs text-brand-ash">
                {connectionStatusLabel(
                  isOnline,
                  wsConnected,
                )}
              </p>


            </div>
          </output>
        )}


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

        {isSecurityOfficer && routePropertyId && (
          <section className="mb-5 rounded-lg border border-border bg-brand-depth p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-semibold text-brand-frost">
                  Active route
                </h2>

                <p className="mt-1 text-xs text-brand-ash">
                  Route from your current location to the
                  selected alert property.
                </p>
              </div>

              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() =>
                  setRoutePropertyId(null)
                }
              >
                Close route
              </Button>
            </div>

            <RouteSummary
              route={route}
              loading={routeLoading}
              error={routeError}
            />
          </section>
        )}


        {loading && mappedAlerts.length === 0 ? (
          <MapLoadingState />
        ) : (
          <CriticalAlertsMap
            alerts={
              showSecurityContent && layerState.liveAlerts
                ? mappedAlerts
                : []
            }
            route={
              showSecurityContent && layerState.routes
                ? route
                : null
            }
            selectedPropertyId={
              routePropertyId ??
              currentSelectedProperty?.propertyId ??
              null
            }
            onSelectProperty={handleSelectProperty}
          />

        )}

        <PropertyAlertsSheet
          property={currentSelectedProperty}
          canShowRoute={isSecurityOfficer}
          open={
            currentSelectedProperty !== null &&
            currentSelectedProperty.alerts.length > 0
          }
          onSelectAlert={setSelectedAlert}
          onClose={() => {
            setSelectedAlert(null);
            setSelectedProperty(null);
          }}
          onShowRoute={(propertyId) => {
            setSelectedAlert(null);
            setRoutePropertyId(propertyId);
            setSelectedProperty(null);
          }}
        />

        {selectedAlert && (
          <AlertDetailSheet
            alert={toAlertDetailModel(selectedAlert)}
            open
            onBack={() => setSelectedAlert(null)}
            onClose={() => setSelectedAlert(null)}
            onAcknowledge={handleAcknowledgeSelectedAlert}
            acknowledging={acknowledgingAlert}
            canViewTracking={isSecurityOfficer}
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
