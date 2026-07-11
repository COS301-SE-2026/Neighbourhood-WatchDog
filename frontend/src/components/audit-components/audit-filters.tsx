"use client"

import { useEffect, useState } from "react"
import { AuditLogsFilters } from "@/lib/api/audit"
import { useDebounce } from "@/hooks/use-debounce"

interface AuditFiltersProps{
    filters: AuditLogsFilters
    onChange: (filters: AuditLogsFilters) => void
}

export function AuditFilters({
    filters, 
    onChange
}: AuditFiltersProps){

    const [rawSearch, setRawSearch] = useState<string>(filters?.searchTerm ?? "")
    const debouncedSearch = useDebounce(rawSearch)

    useEffect(() => {
        onChange({...filters, searchTerm: debouncedSearch})
    }, [debouncedSearch])

    return (
        <div className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 mb-4">
            <input
                className="w-full rounded-md border border-border bg-input px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring focus:border-transparent placeholder:text-muted-foreground"
                type="text"
                onChange={(e) => setRawSearch(e.target.value)} 
                placeholder="Search by ID, Action, Target Entity Type or Target Entity ID field..."
            />
            <div className="flex flex-wrap items-end gap-3">
                <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-muted-foreground">Action</label>
                    <select
                        name="actions"
                        className="rounded-md border border-border bg-input px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                        onChange={(e) => onChange({...filters, action: e.target.value as AuditLogsFilters['action']})}>
                        <option value="UPDATE">UPDATE</option>
                        <option value="CREATE">CREATE</option>
                        <option value="DELETE">DELETE</option>
                    </select>
                </div>
                <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-muted-foreground">From</label>
                    <input  
                        type="datetime-local"
                        className="rounded-md border border-border bg-input px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                        onChange={(e) => onChange({...filters, startDate: e.target.value})}
                    />
                </div>
                <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-muted-foreground">Up to</label>
                    <input
                        type="datetime-local"
                        className="rounded-md border border-border bg-input px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                        onChange={(e) => onChange({...filters, endDate: e.target.value})}
                    />
                </div>
                <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-muted-foreground">Sort</label>
                    <select
                        name="sortOrder"
                        className="rounded-md border border-border bg-input px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                        onChange={(e) => onChange({...filters, sortOrder: e.target.value as AuditLogsFilters['sortOrder']})}>  
                        <option value="ASC">Oldest to newest</option>
                        <option value="DESC">Newest to oldest</option>  
                    </select>
                </div>
            </div>
        </div>
    )
}