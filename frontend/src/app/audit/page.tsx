"use client"

import { useEffect, useState } from "react"
import { DataTable } from "@/components/data-table"
import { AuditLog, PaginatedResponse } from "@/lib/validators/audit"
import { getAuditLogs } from "@/lib/api/audit"
import { ColumnDef } from "@tanstack/react-table"

// export default function Audit(){
//     return (
//         <DataTable ></DataTable>
//     )
// }

const SIZE = 30

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
]

interface PaginationControlsProps{
    nextDisabled: boolean,
    previousDisabled: boolean,
    page: number,
    loading: boolean,
    onPageChange: (newPage: number) => void
}

export function PaginationControls({
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

    return (
        <div>
            { loading && <p>Loading...</p>}
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