"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {
  listNeighbourhoodDispatches,
  type DispatchRecord,
} from "@/lib/api/dispatch";
import {
  DispatchFilters,
  type DispatchFiltersValue,
} from "@/components/dispatch-components/dispatch-filters";
import { DispatchTable } from "@/components/dispatch-components/dispatch-table";

const DEFAULT_FILTERS: DispatchFiltersValue = {
  search: "",
  status: "ALL",
  from: "",
  to: "",
  sort: "NEWEST",
};

export default function DispatchesPage() {
  const params = useParams<{ neighbourhoodId: string }>();
  const neighbourhoodId = params.neighbourhoodId;

  const [dispatches, setDispatches] = useState<DispatchRecord[]>([]);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);
  const [loadedNeighbourhoodId, setLoadedNeighbourhoodId] = useState<
    string | null
  >(null);
  const loading = loadedNeighbourhoodId !== neighbourhoodId;
  const [error, setError] = useState<string | null>(null);
  const visibleError = loadedNeighbourhoodId === neighbourhoodId ? error : null;

  useEffect(() => {
    let cancelled = false;

    listNeighbourhoodDispatches(neighbourhoodId)
      .then((items) => {
        if (cancelled) return;

        setDispatches(items);
        setError(null);
      })
      .catch(() => {
        if (cancelled) return;

        setError("Could not load dispatches.");
      })
      .finally(() => {
        if (!cancelled) {
          setLoadedNeighbourhoodId(neighbourhoodId);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [neighbourhoodId]);

  const filteredDispatches = useMemo(() => {
    const search = filters.search.trim().toLowerCase();
    const fromTime = filters.from
      ? new Date(`${filters.from}T00:00:00`).getTime()
      : null;
    const toTime = filters.to
      ? new Date(`${filters.to}T23:59:59.999`).getTime()
      : null;

    return dispatches
      .filter((dispatch) => {
        if (filters.status !== "ALL" && dispatch.status !== filters.status) {
          return false;
        }

        if (search) {
          const searchable = [
            dispatch.alert_id,
            dispatch.officer_id ?? "",
            dispatch.triggering_sighting_id ?? "",
          ]
            .join(" ")
            .toLowerCase();

          if (!searchable.includes(search)) return false;
        }

        const createdAt = new Date(dispatch.created_at).getTime();

        if (fromTime !== null && createdAt < fromTime) return false;
        if (toTime !== null && createdAt > toTime) return false;

        return true;
      })
      .sort((a, b) => {
        const difference =
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime();

        return filters.sort === "NEWEST" ? -difference : difference;
      });
  }, [dispatches, filters]);

  function handleFiltersChange(nextFilters: DispatchFiltersValue) {
    setFilters(nextFilters);
    setPage(1);
  }

  return (
    <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
      <header className="border-b border-border pb-7">
        <p className="text-sm text-brand-green">Neighbourhood</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
          Dispatches
        </h1>
        <p className="mt-2 max-w-xl text-sm leading-relaxed text-brand-ash">
          Review current and previous officer dispatch attempts.
        </p>
      </header>

      <DispatchFilters filters={filters} onChange={handleFiltersChange} />

      {loading && (
        <div className="flex min-h-40 items-center justify-center">
          <p className="text-sm text-brand-ash">Loading dispatches…</p>
        </div>
      )}

      {visibleError && (
        <p role="alert" className="text-sm text-brand-threat">
          {visibleError}
        </p>
      )}

      {!loading && !error && (
        <DispatchTable
          dispatches={filteredDispatches}
          page={page}
          loading={loading}
          onPageChange={setPage}
        />
      )}
    </main>
  );
}
