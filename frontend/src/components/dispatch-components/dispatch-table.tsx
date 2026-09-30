"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DispatchRecord } from "@/lib/api/dispatch";

type DispatchTableProps = {
  dispatches: DispatchRecord[];
  total: number;
  page: number;
  size: number;
  loading: boolean;
  onPageChange: (page: number) => void;
};

function formatTimestamp(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

export function DispatchTable({
  dispatches,
  total,
  page,
  size,
  loading,
  onPageChange,
}: DispatchTableProps) {
  const pageCount = Math.max(1, Math.ceil(total / size));
  const firstResult = total === 0 ? 0 : (page - 1) * size + 1;
  const lastResult = Math.min(page * size, total);

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
      id: "incident",
      header: "Incident",
      cell: ({ row }) => (
        <div>
          <p className="font-medium text-brand-frost">
            {row.original.detection_type
              ? row.original.detection_type.replaceAll("_", " ").toLowerCase()
              : "Alert"}
          </p>
          <p className="text-xs text-brand-ash">
            {row.original.property_address ?? "Property unavailable"}
            {" · "}
            {row.original.triggering_sighting_id
              ? "Follow-up sighting"
              : "Initial dispatch"}
          </p>
        </div>
      ),
    },
    {
      accessorKey: "officer_name",
      header: "Officer",
      cell: ({ row }) => (
        <span className="text-brand-frost">
          {row.original.officer_name ??
            (row.original.officer_id
              ? "Name unavailable"
              : "No officer assigned")}
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
          <p className="font-medium text-brand-frost">
            {dispatch.detection_type?.replaceAll("_", " ").toLowerCase() ?? "Alert"}
          </p>
          <p>{dispatch.property_address ?? "Property unavailable"}</p>
          <p>
            {dispatch.triggering_sighting_id
              ? "Follow-up sighting"
              : "Initial dispatch"}
          </p>
          <p>
            Officer:{" "}
            {dispatch.officer_name ??
              (dispatch.officer_id ? "Name unavailable" : "No officer assigned")}
          </p>
          <p>Rank: {dispatch.rank ?? "—"}</p>
          <p>Created: {formatTimestamp(dispatch.created_at)}</p>
          <p>Responded: {formatTimestamp(dispatch.responded_at)}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <section aria-label="Dispatch records">
      {dispatches.length === 0 ? (
        <div className="rounded-lg border border-border py-12 text-center text-sm text-brand-ash">
          No dispatches match these filters.
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={dispatches}
          renderMobileCard={renderDispatchCard}
        />
      )}

      <div className="mt-4 flex flex-col items-center justify-between gap-3 sm:flex-row">
        <p className="text-sm text-brand-ash">
          {total === 0
            ? "No dispatches"
            : `Showing ${firstResult}–${lastResult} of ${total}`}
        </p>

        <div className="flex items-center gap-3">
          <button
            type="button"
            disabled={page <= 1 || loading}
            onClick={() => onPageChange(page - 1)}
            className="rounded-md border border-border bg-brand-abyss px-4 py-2 text-sm text-brand-frost transition-colors hover:bg-brand-slate disabled:cursor-not-allowed disabled:opacity-40"
          >
            Previous
          </button>

          <span className="text-sm text-brand-ash">
            Page {page} of {pageCount}
          </span>

          <button
            type="button"
            disabled={page >= pageCount || loading}
            onClick={() => onPageChange(page + 1)}
            className="rounded-md border border-border bg-brand-abyss px-4 py-2 text-sm text-brand-frost transition-colors hover:bg-brand-slate disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
