"use client";

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
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-disabled={disabled}
      disabled={disabled}
      onClick={onChange}
      className={`flex w-full items-center justify-between gap-4 rounded-md border px-3 py-2.5 text-left transition-colors ${
        disabled
          ? "cursor-not-allowed border-border/50 opacity-50"
          : checked
            ? "border-brand-green/40 bg-brand-green/10"
            : "border-border bg-brand-abyss hover:bg-brand-slate"
      }`}
    >
      <span className="min-w-0">
        <span className="block text-sm font-medium text-brand-frost">
          {label}
        </span>

        <span className="mt-0.5 block text-xs text-brand-ash">
          {description}
        </span>
      </span>

      <span
        aria-hidden="true"
        className={`relative h-5 w-9 shrink-0 rounded-full transition-colors ${
          checked ? "bg-brand-green" : "bg-brand-slate"
        }`}
      >
        <span
          className={`absolute top-0.5 size-4 rounded-full bg-white transition-transform ${
            checked ? "translate-x-4" : "translate-x-0.5"
          }`}
        />
      </span>
    </button>
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
      className="rounded-lg border border-border bg-brand-depth p-4"
    >
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-brand-frost">
          Map layers
        </h2>

        <p className="mt-1 text-xs text-brand-ash">
          Choose which information is visible on the map.
        </p>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        <LayerToggle
          label="Properties"
          description="Show all geocoded neighbourhood properties."
          checked={layers.properties}
          onChange={() => onToggle("properties")}
        />

        <LayerToggle
          label="Incident heatmap"
          description="Show aggregated confirmed and resolved incidents."
          checked={layers.heatmap}
          onChange={() => onToggle("heatmap")}
        />

        <LayerToggle
            label="Danger zones"
            description={"Show areas combining incident history and camera sparsity."}
            checked={layers.dangerZones}
            onChange={() => onToggle("dangerZones")}
        />

        <LayerToggle
          label="Contours"
          description="Show contour lines over the incident surface."
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
              description="Show the selected officer route."
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