"use client"

import { useEffect, useState } from "react"
import { DataTable } from "@/components/data-table"
import { AuditLog, PaginatedResponse } from "@/lib/validators/audit"
import { getAuditLogs } from "@/lib/api/audit"
import { ColumnDef } from "@tanstack/react-table"
import { Dialog, DialogContent } from "@/components/ui/dialog"


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

    useEffect(() => {
        
        async function fetchData(){
            setLoading(true)
            try{
                const logs = await getAuditLogs(page, SIZE)
                setAuditLog(logs)
            } catch(e) {
                console.error(e)
            } finally {
                setLoading(false)
            }

        }
        fetchData()
    }, [page])
    
    const data = auditLog?.results ?? []

    const columns: ColumnDef<AuditLog>[] = [
        {
            accessorKey: "id",
            header: "Record ID",
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
                return row.original.timestamp.toLocaleString()
            }
        },
        {
            id: "actions", // this is for the btn
            cell: ({ row }) => {
                return (<button 
                    onClick={() => setSelectedRow(row.original)}>
                    View More
                </button>
                )
                    
            }
        },
    ]

    return (
        <div>
            { loading && <p>Loading...</p>}
            <Dialog open={!!selectedRow} onOpenChange={(open) => setSelectedRow(null)}>
                <DialogContent>
                    {selectedRow && (
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
                    )}
                </DialogContent>
            </Dialog>
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