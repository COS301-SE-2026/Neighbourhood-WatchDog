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
          className="bg-navy text-white rounded-lg w-25 p-2 disabled:bg-muted"
          disabled={previousDisabled || loading}
          onClick={() => onPageChange(page - 1)}>
          Previous
        </button>
        <button 
          className="bg-navy text-white rounded-lg w-25 p-2 disabled:bg-muted"
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
    <Card>
      <CardHeader>
        <CardTitle>
          {rowData.action} on {rowData.target_entity_type}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {rowData.id.slice(0, 12) + "..."} at {formatTimestamp(rowData.timestamp)}
        <button className="rounded-lg bg-navy text-white p-2" onClick={() => setSelectedRow(rowData)}>
          View More
        </button>
      </CardContent>
    </Card>
  )
}


  const columns: ColumnDef<AuditLog>[] = [
    {
      accessorKey: "id",
      header: "Record ID",
      cell: ({row}) => {
        {return row.original.id.slice(0, 8) + "..."}
      }
    },
    {
      accessorKey: "action",
      header: "Action",
    },
    {
      accessorKey: "target_entity_type",
      header: "Target Entity Type",
    },
    {
      accessorKey: "timestamp",
      header: "Timestamp",
      cell: ({ row }) => {
        return formatTimestamp(row.original.timestamp)
      }
    },
    {
      id: "actions", // this is for the btn
      cell: ({ row }) => {
        return (
        <button className="rounded-lg bg-navy text-white p-2" onClick={() => setSelectedRow(row.original)}>
          View More
        </button>
        )
      }
    },
  ]

  return (
    <div className="bg-background rounded-radius-sm p-20 w-full max-w-full overflow-x-auto">
      { loading && <p>Loading...</p>}
      <Dialog open={!!selectedRow} onOpenChange={() => setSelectedRow(null)}>
        <DialogContent>
          {selectedRow && (
            <div>
              <DialogTitle className="font-bold">Record Details</DialogTitle>
              <ul>
                <li>User ID: {selectedRow.user_id}</li>
                <li>Target Entity ID: {selectedRow.target_entity_id}</li>
                <li>Old values: <pre> {selectedRow.old_values ? JSON.stringify(selectedRow.old_values, null, 4) : "No old values"} </pre> </li>
                <li>New values: <pre> {selectedRow.new_values ? JSON.stringify(selectedRow.new_values, null, 4) : "No new values"} </pre> </li>
              </ul>
            </div>
          )}
        </DialogContent>
      </Dialog>
      <AuditFilters filters={filters} onChange={(filters: AuditLogsFilters) => {setLoading(true); setFilters(filters)}}/>
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