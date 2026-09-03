"use client"

import { useEffect, useState } from "react"
import { DataTable } from "@/components/data-table"
import { AuditLog, PaginatedResponse } from "@/lib/validators/audit"
import { AuditLogsFilters, getAuditLogs } from "@/lib/api/audit"
import { ColumnDef } from "@tanstack/react-table"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { AuditFilters } from "./audit-filters"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card"

const SIZE = 30


interface PaginationControlsProps{
  nextDisabled: boolean,
  previousDisabled: boolean,
  page: number,
  loading: boolean,
  onPageChange: (newPage: number) => void
}

export default function PaginationControls({
  nextDisabled,
  previousDisabled,
  page,
  loading,
  onPageChange    
}: PaginationControlsProps) {
  return (
    <div className="flex flex-col justfy-around">
      <div className="flex justify-around pt-5"><p>Page {page}</p></div>
      <div className="flex justify-around p-2">
        <button 
          className="rounded-md border border-border bg-brand-abyss px-4 py-2 text-sm text-brand-frost transition-colors hover:bg-brand-slate disabled:cursor-not-allowed disabled:opacity-40"

          disabled={previousDisabled || loading}
          onClick={() => onPageChange(page - 1)}>
          Previous
        </button>
        <button 
          className="rounded-md border border-border bg-brand-abyss px-4 py-2 text-sm text-brand-frost transition-colors hover:bg-brand-slate disabled:cursor-not-allowed disabled:opacity-40"

          disabled={nextDisabled || loading}
          onClick={() => onPageChange(page + 1)}
          >Next
        </button>
      </div>
    </div>
  )
}

function formatTimestamp(date: Date){
  const day = date.getDate()
  const month = date.getMonth() + 1
  const year = date.getFullYear()
  const hours = date.getHours().toString().padStart(2, "0")
  const minutes = date.getMinutes().toString().padStart(2, "0")
  return `${day}/${month}/${year} ${hours}:${minutes}`
}

export function AuditLogTable() {
  const [page, setPage] = useState<number>(1)
  const [auditLog, setAuditLog] = useState<PaginatedResponse<AuditLog>|null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [selectedRow, setSelectedRow] = useState<AuditLog | null>(null)
  const [filters, setFilters] = useState<AuditLogsFilters>({})

  useEffect(() => {
    let ignore = false

    async function fetchData(){
      try{
        const logs = await getAuditLogs(page, SIZE, filters)
        if (!ignore) {
          setAuditLog(logs)
        }        
      } catch(e) {
        console.error(e)
      } finally {
        if (!ignore){
          setLoading(false)
        }

      }
    }

    fetchData()

    return () => {
      ignore = true
    }
  }, [page, filters])
  
  const data = auditLog?.results ?? []

  function renderAuditLogCard(rowData: AuditLog): React.ReactNode {
  return (
    <Card className="border-border bg-brand-abyss text-brand-frost">
      <CardHeader>
        <CardTitle className="text-brand-frost">
          {rowData.action} on {rowData.target_entity_type}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-brand-ash">
        {rowData.id.slice(0, 12) + "..."} at {formatTimestamp(rowData.timestamp)}
        <button className="rounded-lg bg-brand-abyss text-brand-frost p-2" onClick={() => setSelectedRow(rowData)}>
          View More
        </button>
      </CardContent>
    </Card>
  )
}


  const columns: ColumnDef<AuditLog>[] = [
    {
      accessorKey: "id",
      header: () => (
        <span className="!text-brand-frost">
          Record ID
        </span>
      ),
      cell: ({ row }) => (
        <span className="!text-brand-frost">
          {row.original.id.slice(0, 8) + "..."}
        </span>
      ),
    },
    {
      accessorKey: "action",
      header: () => (
        <span className="!text-brand-frost">
          Action
        </span>
      ),
      cell: ({ row }) => (
        <span className="!text-brand-frost">
          {row.original.action}
        </span>
      ),
    },
    {
      accessorKey: "target_entity_type",
      header: () => (
        <span className="!text-brand-frost">
          Target Entity Type
        </span>
      ),
      cell: ({ row }) => (
        <span className="!text-brand-frost">
          {row.original.target_entity_type}
        </span>
      ),
    },
    {
      accessorKey: "timestamp",
      header: () => (
        <span className="!text-brand-frost">
          Timestamp
        </span>
      ),
      cell: ({ row }) => {
        return (
          <span className="!text-brand-frost">
            {formatTimestamp(row.original.timestamp)}
          </span>
        )
      }
    },
    {
      id: "actions", // this is for the btn
      header: () => (
        <span className="!text-brand-frost">
          Actions
        </span>
      ),
      cell: ({ row }) => {
        return (
        <button className="rounded-lg bg-brand-abyss text-brand-frost p-2" onClick={() => setSelectedRow(row.original)}>
          View More
        </button>
        )
      }
    },
  ]


  return (
    <div className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
      {loading && (
          <div className="flex min-h-40 items-center justify-center">
              <p className="text-sm text-brand-ash">Loading audit logs...</p>
          </div>
      )}

      <Dialog open={!!selectedRow} onOpenChange={() => setSelectedRow(null)}>
        <DialogContent className="max-w-2xl border-border bg-brand-abyss text-brand-frost">
          {selectedRow && (
            <div className="space-y-6">
              <div>
                <DialogTitle className="text-lg font-semibold text-brand-frost">
                  Record details
                </DialogTitle>
                <p className="mt-1 text-sm text-brand-ash">
                  {selectedRow.action} on {selectedRow.target_entity_type}
                </p>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-brand-ash/70">
                    User ID
                  </p>
                  <p className="mt-1 break-all text-sm text-brand-ash">
                    {selectedRow.user_id}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-brand-ash/70">
                    Target entity ID
                  </p>
                  <p className="mt-1 break-all text-sm text-brand-ash">
                    {selectedRow.target_entity_id ?? "No target entity"}
                  </p>
                </div>
              </div>

              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-brand-ash/70">
                  Previous values
                </p>
                <pre className="max-h-60 overflow-auto rounded-md border border-border bg-brand-void p-4 text-xs leading-relaxed text-brand-ash">
                  {selectedRow.old_values
                    ? JSON.stringify(selectedRow.old_values, null, 2)
                    : "No previous values"}
                </pre>
              </div>

              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-brand-ash/70">
                  New values
                </p>
                <pre className="max-h-60 overflow-auto rounded-md border border-border bg-brand-void p-4 text-xs leading-relaxed text-brand-ash">
                  {selectedRow.new_values
                    ? JSON.stringify(selectedRow.new_values, null, 2)
                    : "No new values"}
                </pre>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      <header className="border-b border-border pb-7">
          <p className="text-sm text-brand-green">System</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
              Neighbourhood audit logs
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-brand-ash">
              Review activity recorded across the neighbourhood system.
          </p>
      </header>

      <AuditFilters
          filters={filters}
          onChange={(newFilters: AuditLogsFilters) => {
              setLoading(true);
              setPage(1);
              setFilters(newFilters);
          }}
      />

      <DataTable columns={columns} data={data} renderMobileCard={renderAuditLogCard}/>
      <PaginationControls 
        previousDisabled={page==1}
        nextDisabled={page * SIZE >= (auditLog?.total ?? 0)}
        page={page}
        loading={loading}
        onPageChange={(newPage) => {setLoading(true); setPage(newPage)}} />
    </div>
  )
}