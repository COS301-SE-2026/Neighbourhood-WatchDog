"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  listNeighbourhoodDispatches,
  type DispatchListFilters,
  type DispatchPage,
} from "@/lib/api/dispatch";
import { DispatchFilters } from "@/components/dispatch-components/dispatch-filters";
import { DispatchTable } from "@/components/dispatch-components/dispatch-table";

const PAGE_SIZE = 20;

const DEFAULT_FILTERS: DispatchListFilters = {
  search: "",
  status: "ALL",
  from: "",
  to: "",
  sort: "NEWEST",
};

export default function DispatchesPage() {
  const params = useParams<{ neighbourhoodId: string }>();
  const neighbourhoodId = params.neighbourhoodId;

  const [filters, setFilters] = useState<DispatchListFilters>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);
  const [pageData, setPageData] = useState<DispatchPage | null>(null);
  const [loadedRequestKey, setLoadedRequestKey] = useState<string | null>(null);
  const [errorState, setErrorState] = useState<{
    key: string;
    message: string;
  } | null>(null);

  const requestKey = JSON.stringify([
    neighbourhoodId,
    page,
    PAGE_SIZE,
    filters.status,
    filters.search,
    filters.from,
    filters.to,
    filters.sort,
  ]);

  const loading = loadedRequestKey !== requestKey;
  const visibleError =
    errorState?.key === requestKey ? errorState.message : null;

  useEffect(() => {
    let cancelled = false;

    listNeighbourhoodDispatches(neighbourhoodId, page, PAGE_SIZE, filters)
      .then((result) => {
        if (cancelled) return;

        setPageData(result);
        setErrorState(null);
        setLoadedRequestKey(requestKey);
      })
      .catch(() => {
        if (cancelled) return;

        setErrorState({
          key: requestKey,
          message: "Could not load dispatches.",
        });
        setLoadedRequestKey(requestKey);
      });

    return () => {
      cancelled = true;
    };
  }, [neighbourhoodId, page, filters, requestKey]);

  function handleFiltersChange(nextFilters: DispatchListFilters) {
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

      {!loading && !visibleError && (
        <DispatchTable
          dispatches={pageData?.results ?? []}
          total={pageData?.total ?? 0}
          page={page}
          size={PAGE_SIZE}
          loading={loading}
          onPageChange={setPage}
        />
      )}
    </main>
  );
}
