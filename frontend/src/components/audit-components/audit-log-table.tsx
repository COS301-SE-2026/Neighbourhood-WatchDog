"use client"

import { useEffect, useState } from "react"
import { DataTable } from "@/components/data-table"
import { AuditLog, PaginatedResponse } from "@/lib/validators/audit"
import { AuditLogsFilters, getAuditLogs } from "@/lib/api/audit"
import { ColumnDef } from "@tanstack/react-table"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { AuditFilters } from "./audit-filters"

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
        <div>
            <button 
                disabled={previousDisabled || loading}
                onClick={() => onPageChange(page - 1)}>
                Previous
            </button>
            <button 
                disabled={nextDisabled || loading}
                onClick={() => onPageChange(page + 1)}
                >Next
            </button>
        </div>
    )
}

export function AuditLogTable() {
    const [page, setPage] = useState<number>(1)
    const [auditLog, setAuditLog] = useState<PaginatedResponse<AuditLog>|null>(null)
    const [loading, setLoading] = useState<boolean>(true)
    const [selectedRow, setSelectedRow] = useState<AuditLog | null>(null)


    async function fetchData(filters?: AuditLogsFilters){
        setLoading(true)
        try{
            const logs = await getAuditLogs(page, SIZE, filters)
            setAuditLog(logs)
        } catch(e) {
            console.error(e)
        } finally {
            setLoading(false)
        }

    }

    useEffect(() => {
        fetchData()
    }, [page])
    
    const data = auditLog?.results ?? []

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
                const day = row.original.timestamp.getDate()
                const month = row.original.timestamp.getMonth() + 1
                const year = row.original.timestamp.getFullYear()
                const hours = row.original.timestamp.getHours()
                const minutes = row.original.timestamp.getMinutes()
                return `${day}/${month}/${year} ${hours}:${minutes}`
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
            <Dialog open={!!selectedRow} onOpenChange={(open) => setSelectedRow(null)}>
                <DialogContent>
                    {selectedRow && (
                        <div>
                            <DialogTitle className="font-bold">Record Details</DialogTitle>
                            <ul>
                                <li>User ID: {selectedRow.user_id}</li>
                                <li>Target Entity ID: {selectedRow.target_entity_id}</li>
                                <li>Old values: 
                                    <pre>
                                        {selectedRow.old_values ? JSON.stringify(selectedRow.old_values, null, 4) : "No old values"}
                                    </pre>
                                </li>
                                <li>New values: 
                                    <pre>
                                        {selectedRow.new_values ? JSON.stringify(selectedRow.new_values, null, 4) : "No new values"}
                                    </pre>
                                </li>
                            </ul>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
            <AuditFilters onChange={fetchData}/>
            <DataTable columns={columns} data={data} />
            <PaginationControls 
                previousDisabled={page==1}
                nextDisabled={page * SIZE >= (auditLog?.total ?? 0)}
                page={page}
                loading={loading}
                onPageChange={(newPage) => {setPage(newPage)}} />
        </div>
    )
}