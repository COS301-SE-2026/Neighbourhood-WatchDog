"use client";

import { useMemo } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DispatchRecord } from "@/lib/api/dispatch";

const PAGE_SIZE = 20;

type DispatchTableProps = {
  dispatches: DispatchRecord[];
  page: number;
  loading: boolean;
  onPageChange: (page: number) => void;
};

function formatTimestamp(value: string | null) {
  if (!value) return "—";

  return new Date(value).toLocaleString();
}

function shortId(value: string | null, length = 8) {
  return value ? `${value.slice(0, length)}…` : "None";
}

export function DispatchTable({
  dispatches,
  page,
  loading,
  onPageChange,
}: DispatchTableProps) {
  const pageCount = Math.max(1, Math.ceil(dispatches.length / PAGE_SIZE));
  const visiblePage = Math.min(page, pageCount);

  const pageDispatches = useMemo(() => {
    const start = (visiblePage - 1) * PAGE_SIZE;
    return dispatches.slice(start, start + PAGE_SIZE);
  }, [dispatches, visiblePage]);

  const columns: ColumnDef<DispatchRecord>[] = [
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => (
        <span className="font-medium text-brand-frost">
          {row.original.status.replaceAll("_", " ")}
        </span>
      ),
    },
    {
      accessorKey: "alert_id",
      header: "Alert",
      cell: ({ row }) => (
        <span
          className="font-mono text-xs text-brand-ash"
          title={row.original.alert_id}
        >
          {shortId(row.original.alert_id)}
        </span>
      ),
    },
    {
      accessorKey: "triggering_sighting_id",
      header: "Sighting",
      cell: ({ row }) => {
        const sightingId = row.original.triggering_sighting_id;

        return sightingId ? (
          <span className="font-mono text-xs text-brand-ash" title={sightingId}>
            {shortId(sightingId)}
          </span>
        ) : (
          <span className="text-brand-ash">Initial dispatch</span>
        );
      },
    },
    {
      accessorKey: "officer_id",
      header: "Officer",
      cell: ({ row }) => (
        <span
          className="font-mono text-xs text-brand-ash"
          title={row.original.officer_id ?? "No officer assigned"}
        >
          {shortId(row.original.officer_id)}
        </span>
      ),
    },
    {
      accessorKey: "rank",
      header: "Rank",
      cell: ({ row }) => row.original.rank ?? "—",
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => formatTimestamp(row.original.created_at),
    },
    {
      accessorKey: "responded_at",
      header: "Responded",
      cell: ({ row }) => formatTimestamp(row.original.responded_at),
    },
  ];

  function renderDispatchCard(dispatch: DispatchRecord) {
    return (
      <Card className="border-border bg-brand-abyss text-brand-frost">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            {dispatch.status.replaceAll("_", " ")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-brand-ash">
          <p>
            Alert:{" "}
            <span className="font-mono">{shortId(dispatch.alert_id)}</span>
          </p>
          <p>
            Sighting:{" "}
            {dispatch.triggering_sighting_id ? (
              <span
                className="font-mono"
                title={dispatch.triggering_sighting_id}
              >
                {shortId(dispatch.triggering_sighting_id)}
              </span>
            ) : (
              "Initial dispatch"
            )}
          </p>
          <p>
            Officer:{" "}
            <span className="font-mono">{shortId(dispatch.officer_id)}</span>
          </p>
          <p>Rank: {dispatch.rank ?? "—"}</p>
          <p>Created: {formatTimestamp(dispatch.created_at)}</p>
          <p>Responded: {formatTimestamp(dispatch.responded_at)}</p>
        </CardContent>
      </Card>
    );
  }

  const firstResult =
    dispatches.length === 0 ? 0 : (visiblePage - 1) * PAGE_SIZE + 1;
  const lastResult = Math.min(visiblePage * PAGE_SIZE, dispatches.length);

  return (
    <section aria-label="Dispatch records">
      {dispatches.length === 0 ? (
        <div className="rounded-lg border border-border py-12 text-center text-sm text-brand-ash">
          No dispatches match these filters.
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={pageDispatches}
          renderMobileCard={renderDispatchCard}
        />
      )}

      <div className="mt-4 flex flex-col items-center justify-between gap-3 sm:flex-row">
        <p className="text-sm text-brand-ash">
          {dispatches.length === 0
            ? "No dispatches"
            : `Showing ${firstResult}–${lastResult} of ${dispatches.length}`}
        </p>

        <div className="flex items-center gap-3">
          <button
            type="button"
            disabled={visiblePage <= 1 || loading}
            onClick={() => onPageChange(visiblePage - 1)}
            className="rounded-md border border-border bg-brand-abyss px-4 py-2 text-sm text-brand-frost transition-colors hover:bg-brand-slate disabled:cursor-not-allowed disabled:opacity-40"
          >
            Previous
          </button>

          <span className="text-sm text-brand-ash">
            Page {visiblePage} of {pageCount}
          </span>

          <button
            type="button"
            disabled={visiblePage >= pageCount || loading}
            onClick={() => onPageChange(visiblePage + 1)}
            className="rounded-md border border-border bg-brand-abyss px-4 py-2 text-sm text-brand-frost transition-colors hover:bg-brand-slate disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
