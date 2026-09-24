"use client";

export type MapMode = "neighbourhood" | "security";

interface MapModeTabsProps {
  readonly mode: MapMode;
  readonly securityAvailable: boolean;
  readonly onChange: (mode: MapMode) => void;
}

export function MapModeTabs({
  mode,
  securityAvailable,
  onChange,
}: MapModeTabsProps) {
  return (
    <div
      className="inline-flex rounded-lg border border-border bg-brand-depth p-1"
      role="tablist"
      aria-label="Map view"
    >
      <button
        type="button"
        role="tab"
        aria-selected={mode === "neighbourhood"}
        onClick={() => onChange("neighbourhood")}
        className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
          mode === "neighbourhood"
            ? "bg-brand-green text-brand-void"
            : "text-brand-ash hover:bg-brand-slate hover:text-brand-frost"
        }`}
      >
        Neighbourhood
      </button>

      {securityAvailable && (
        <button
          type="button"
          role="tab"
          aria-selected={mode === "security"}
          onClick={() => onChange("security")}
          className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            mode === "security"
              ? "bg-brand-threat text-white"
              : "text-brand-ash hover:bg-brand-slate hover:text-brand-frost"
          }`}
        >
          Security
        </button>
      )}
    </div>
  );
}