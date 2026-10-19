"use client";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export type MapLayerKey =
  | "properties"
  | "heatmap"
  | "dangerZones"
  | "contours"
  | "liveAlerts"
  | "routes";

export type MapLayerState = Record<MapLayerKey, boolean>;

interface MapLayerControlsProps {
  readonly layers: MapLayerState;
  readonly showSecurityLayers: boolean;
  readonly canViewRoutes: boolean;
  readonly onToggle: (layer: MapLayerKey) => void;
}

interface LayerToggleProps {
  readonly label: string;
  readonly description: string;
  readonly checked: boolean;
  readonly onChange: () => void;
  readonly disabled?: boolean;
}

function LayerToggle({
  label,
  description,
  checked,
  onChange,
  disabled = false,
}: LayerToggleProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          role="switch"
          aria-label={label}
          aria-checked={checked}
          aria-disabled={disabled}
          onClick={disabled ? undefined : onChange}
          className={`inline-flex min-h-9 items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs font-medium text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green/50 ${
            disabled
              ? "cursor-not-allowed border-border/50 opacity-50"
              : checked
                ? "border-brand-green/40 bg-brand-green/10 text-brand-frost"
                : "border-border bg-brand-abyss text-brand-ash hover:bg-brand-slate hover:text-brand-frost"
          }`}
        >
          <span>{label}</span>

          <span
            aria-hidden="true"
            className={`relative h-4 w-7 shrink-0 rounded-full transition-colors ${
              checked ? "bg-brand-green" : "bg-brand-slate"
            }`}
          >
            <span
              className={`absolute top-0.5 size-3 rounded-full bg-white transition-transform ${
                checked ? "translate-x-3.5" : "translate-x-0.5"
              }`}
            />
          </span>
        </button>
      </TooltipTrigger>

      <TooltipContent side="top" sideOffset={6}>
        {description}
      </TooltipContent>
    </Tooltip>
  );
}

export function MapLayerControls({
  layers,
  showSecurityLayers,
  canViewRoutes,
  onToggle,
}: MapLayerControlsProps) {
  return (
    <section
      aria-label="Map layer controls"
      className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-brand-depth p-2"
    >
      <h2 className="px-1 text-xs font-semibold text-brand-ash">
        Map layers
      </h2>

      <div className="flex flex-wrap items-center gap-1.5">
        <LayerToggle
          label="Properties"
          description="Show all geocoded neighbourhood properties."
          checked={layers.properties}
          onChange={() => onToggle("properties")}
        />

        <LayerToggle
          label="Incident heatmap"
          description="Show aggregated confirmed and resolved incidents for the selected date range."
          checked={layers.heatmap}
          onChange={() => onToggle("heatmap")}
        />

        <LayerToggle
          label="Danger zones"
          description="Show areas combining incident history and camera sparsity."
          checked={layers.dangerZones}
          onChange={() => onToggle("dangerZones")}
        />

        <LayerToggle
          label="Contours"
          description="Show contour lines over the historical incident surface for the selected date range."
          checked={layers.contours}
          onChange={() => onToggle("contours")}
        />

        {showSecurityLayers && (
          <>
            <LayerToggle
              label="Live alerts"
              description="Show individual active alert markers."
              checked={layers.liveAlerts}
              onChange={() => onToggle("liveAlerts")}
            />

            <LayerToggle
              label="Routes"
              description={
                canViewRoutes
                  ? "Show the selected officer route."
                  : "Officer routes are only available to users with route access."
              }
              checked={layers.routes}
              disabled={!canViewRoutes}
              onChange={() => onToggle("routes")}
            />
          </>
        )}
      </div>
    </section>
  );
}