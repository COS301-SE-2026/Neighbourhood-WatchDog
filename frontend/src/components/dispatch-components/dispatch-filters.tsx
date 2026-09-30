"use client";

import type { DispatchListFilters, DispatchStatus } from "@/lib/api/dispatch";

type DispatchFiltersProps = {
  filters: DispatchListFilters;
  onChange: (filters: DispatchListFilters) => void;
};

const STATUSES: DispatchStatus[] = [
  "SELECTED",
  "PENDING",
  "QUEUED",
  "NOTIFIED",
  "ACCEPTED",
  "DECLINED",
  "TIMED_OUT",
  "NO_CANDIDATE",
];

export function DispatchFilters({ filters, onChange }: DispatchFiltersProps) {
  function update(change: Partial<DispatchListFilters>) {
    onChange({ ...filters, ...change });
  }

  return (
    <section
      aria-label="Filter dispatches"
      className="mb-6 flex flex-col gap-4 border-b border-border py-6"
    >
      <label className="flex flex-col gap-1 text-sm font-medium text-brand-frost">
        Search
        <input
          type="search"
          value={filters.search}
          onChange={(event) => update({ search: event.target.value })}
          placeholder="Alert, officer, or sighting ID"
          className="h-10 w-full rounded-md border border-border bg-brand-abyss px-3 text-sm font-normal text-brand-frost outline-none placeholder:text-brand-ash/60 focus:border-brand-green/60"
        />
      </label>

      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1 text-sm font-medium text-brand-frost">
          Status
          <select
            value={filters.status}
            onChange={(event) =>
              update({
                status: event.target.value as DispatchListFilters["status"],
              })
            }
            className="h-10 rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-frost outline-none [color-scheme:dark] focus:border-brand-green/60"
          >
            <option value="ALL">All statuses</option>
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {status.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium text-brand-frost">
          From
          <input
            type="date"
            value={filters.from}
            onChange={(event) => update({ from: event.target.value })}
            className="h-10 rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-frost outline-none [color-scheme:dark] focus:border-brand-green/60"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium text-brand-frost">
          To
          <input
            type="date"
            value={filters.to}
            onChange={(event) => update({ to: event.target.value })}
            className="h-10 rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-frost outline-none [color-scheme:dark] focus:border-brand-green/60"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium text-brand-frost">
          Sort
          <select
            value={filters.sort}
            onChange={(event) =>
              update({
                sort: event.target.value as DispatchListFilters["sort"],
              })
            }
            className="h-10 rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-frost outline-none [color-scheme:dark] focus:border-brand-green/60"
          >
            <option value="NEWEST">Newest first</option>
            <option value="OLDEST">Oldest first</option>
          </select>
        </label>

        <button
          type="button"
          onClick={() =>
            onChange({
              search: "",
              status: "ALL",
              from: "",
              to: "",
              sort: "NEWEST",
            })
          }
          className="h-10 rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-ash transition-colors hover:bg-brand-slate hover:text-brand-frost"
        >
          Clear filters
        </button>
      </div>
    </section>
  );
}
