"use client";

import { useCallback, useMemo, useState } from "react";
import {
  AlertCard,
  type Alert,
  type AlertSeverity,
  type AlertStatus,
  getSeverity,
} from "@/components/shared/AlertCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SlidersHorizontal, RefreshCw } from "lucide-react";

const ALL_SEVERITIES: AlertSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const ALL_STATUSES: AlertStatus[] = ["NEW", "ACKNOWLEDGED", "RESOLVED"];

const SEVERITY_LABELS: Record<AlertSeverity, string> = {
  CRITICAL: "Critical",
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
};

const STATUS_LABELS: Record<AlertStatus, string> = {
  NEW: "New",
  ACKNOWLEDGED: "Acknowledged",
  RESOLVED: "Resolved",
};

function EmptyState() {
  return (
    <div
      className="flex flex-col items-center justify-center py-20 text-center"
      role="status"
      aria-live="polite"
    >
      <p className="text-[15px] font-semibold text-white/60">No alerts</p>
    </div>
  );
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>(MOCK_ALERTS);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedSeverities, setSelectedSeverities] = useState<
    Set<AlertSeverity>
  >(new Set(ALL_SEVERITIES));
  const [selectedStatuses, setSelectedStatuses] = useState<Set<AlertStatus>>(
    new Set(["NEW", "ACKNOWLEDGED"]),
  );

  const handleAcknowledge = useCallback(async (id: string) => {
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === id ? { ...a, status: "ACKNOWLEDGED" as AlertStatus } : a,
      ),
    );
  }, []);

  function handleRefresh() {
    setAlerts(MOCK_ALERTS);
    setRefreshKey((k) => k + 1);
  }

  const filtered = useMemo(
    () =>
      alerts.filter((a) => {
        const sev = getSeverity(a.detection_type);
        return (
          selectedSeverities.has(sev) &&
          selectedStatuses.has(a.status as AlertStatus)
        );
      }),
    [alerts, selectedSeverities, selectedStatuses],
  );

  // active = user has deviated from the default (new + acknowledged, all severities)
  const hasActiveFilters =
    selectedSeverities.size < ALL_SEVERITIES.length ||
    !selectedStatuses.has("NEW") ||
    !selectedStatuses.has("ACKNOWLEDGED") ||
    selectedStatuses.has("RESOLVED");

  const newCount = alerts.filter((a) => a.status === "NEW").length;
  const criticalCount = alerts.filter(
    (a) => getSeverity(a.detection_type) === "CRITICAL" && a.status === "NEW",
  ).length;

  return (
    // TooltipProvider wraps the tree because AlertCard uses Radix tooltips internally
    <TooltipProvider>
      {/*
        Using w-full + flex here so this page fills whatever space the parent layout
        gives it (i.e. the content area to the right of the sidebar), rather than
        trying to be min-h-screen and centering against the full viewport width.
      */}
      <div
        className="w-full flex flex-col items-center px-8 py-10 bg-[#1D2A5E] min-h-full"
        style={{
          fontFamily: "var(--font-sans, 'Inter', system-ui, sans-serif)",
        }}
      >
        <div className="w-full max-w-2xl">
          <header className="mb-6 text-center">
            <h1 className="text-[32px] font-bold leading-10 text-white">
              Alerts
            </h1>

            {(newCount > 0 || criticalCount > 0) && (
              <div
                className="flex gap-2 mt-3 flex-wrap justify-center"
                aria-live="polite"
              >
                {newCount > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold bg-[#3B5EDE]/20 border border-[#3B5EDE]/30 rounded-full px-3 py-1 text-[#5B8DEF]">
                    {newCount} new
                  </span>
                )}
                {criticalCount > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold bg-[#DC2626]/20 border border-[#DC2626]/30 rounded-full px-3 py-1 text-[#DC2626]">
                    {criticalCount} critical
                  </span>
                )}
              </div>
            )}
          </header>

          {/*
            rounded-2xl needs to be paired with overflow-hidden carefully — overflow-hidden
            clips the corners but also clips box-shadows and focus rings on children.
            Instead we let the card round its own corners and handle inner border-radius
            on the toolbar/list sections manually.
          */}
          <Card className="bg-[#2C3E6B]/40 border-[#2C3E6B] rounded-2xl">
            <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-[#2C3E6B] rounded-t-2xl">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className={[
                      "border-[#2C3E6B] bg-transparent text-[#D0D7E8] hover:bg-[#2C3E6B] hover:text-white transition-colors text-xs font-medium",
                      hasActiveFilters
                        ? "border-[#3B5EDE]/60 text-[#5B8DEF]"
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    aria-label="Open filter options"
                  >
                    <SlidersHorizontal className="h-3.5 w-3.5 mr-1.5" />
                    Filter
                    {hasActiveFilters && (
                      <span className="ml-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#3B5EDE] text-[9px] font-bold text-white">
                        !
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="start"
                  className="w-52 bg-[#1D2A5E] border-[#2C3E6B] text-white"
                >
                  <DropdownMenuLabel className="text-[#D0D7E8]/60 text-[10px] uppercase tracking-wider">
                    Severity
                  </DropdownMenuLabel>
                  {ALL_SEVERITIES.map((sev) => (
                    <DropdownMenuCheckboxItem
                      key={sev}
                      className="text-sm text-white focus:bg-[#2C3E6B] focus:text-white cursor-pointer"
                      checked={selectedSeverities.has(sev)}
                      onCheckedChange={(checked) => {
                        setSelectedSeverities((prev) => {
                          const next = new Set(prev);
                          checked ? next.add(sev) : next.delete(sev);
                          return next;
                        });
                      }}
                    >
                      {SEVERITY_LABELS[sev]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  <DropdownMenuSeparator className="bg-[#2C3E6B]" />

                  <DropdownMenuLabel className="text-[#D0D7E8]/60 text-[10px] uppercase tracking-wider">
                    Status
                  </DropdownMenuLabel>
                  {ALL_STATUSES.map((st) => (
                    <DropdownMenuCheckboxItem
                      key={st}
                      className="text-sm text-white focus:bg-[#2C3E6B] focus:text-white cursor-pointer"
                      checked={selectedStatuses.has(st)}
                      onCheckedChange={(checked) => {
                        setSelectedStatuses((prev) => {
                          const next = new Set(prev);
                          checked ? next.add(st) : next.delete(st);
                          return next;
                        });
                      }}
                    >
                      {STATUS_LABELS[st]}
                    </DropdownMenuCheckboxItem>
                  ))}

                  {hasActiveFilters && (
                    <>
                      <DropdownMenuSeparator className="bg-[#2C3E6B]" />
                      <button
                        onClick={() => {
                          setSelectedSeverities(new Set(ALL_SEVERITIES));
                          setSelectedStatuses(new Set(["NEW", "ACKNOWLEDGED"]));
                        }}
                        className="w-full text-left px-2 py-1.5 text-xs text-[#5B8DEF] hover:text-white transition-colors"
                      >
                        Clear all filters
                      </button>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                className="text-[#5B8DEF] hover:text-white hover:bg-[#2C3E6B] transition-colors text-xs"
                aria-label="Refresh alerts"
              >
                <RefreshCw key={refreshKey} className="h-3.5 w-3.5 mr-1.5" />
                Refresh
              </Button>
            </div>

            <section
              aria-label="Alert list"
              aria-live="polite"
              className="p-4 rounded-b-2xl"
            >
              {filtered.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-3">
                  {filtered.map((alert) => (
                    <AlertCard
                      key={alert.id}
                      alert={alert}
                      onAcknowledge={handleAcknowledge}
                    />
                  ))}
                </div>
              )}
            </section>
          </Card>
        </div>
      </div>
    </TooltipProvider>
  );
}
