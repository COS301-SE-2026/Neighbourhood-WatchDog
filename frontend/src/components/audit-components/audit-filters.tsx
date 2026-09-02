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
        <div className="mb-6 flex flex-col gap-5 border-b border-white/10 py-6">
            <input
                className="h-10 w-full rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-emerald-500/60"
                type="text"
                onChange={(e) => setRawSearch(e.target.value)} 
                placeholder="Search by ID, Action, Target Entity Type or Target Entity ID field..."
            />
            <div className="flex flex-wrap items-end gap-5">
                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-white">Action</label>
                    <select
                        name="actions"
                        className="h-10 rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none [color-scheme:dark] focus:border-emerald-500/60"
                        onChange={(e) => onChange({...filters, action: e.target.value as AuditLogsFilters['action']})}>
                        <option value="UPDATE">UPDATE</option>
                        <option value="CREATE">CREATE</option>
                        <option value="DELETE">DELETE</option>
                    </select>
                </div>
                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-white">From</label>
                    <input  
                        type="datetime-local"
                        className="h-10 rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none [color-scheme:dark] focus:border-emerald-500/60"
                        onChange={(e) => onChange({...filters, startDate: e.target.value})}
                    />
                </div>
                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-white">Up to</label>
                    <input
                        type="datetime-local"
                        className="h-10 rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none [color-scheme:dark] focus:border-emerald-500/60"
                        onChange={(e) => onChange({...filters, endDate: e.target.value})}
                    />
                </div>
                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-white">Sort</label>
                    <select
                        name="sortOrder"
                        className="h-10 rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none [color-scheme:dark] focus:border-emerald-500/60"
                        onChange={(e) => onChange({...filters, sortOrder: e.target.value as AuditLogsFilters['sortOrder']})}>  
                        <option value="ASC">Oldest to newest</option>
                        <option value="DESC">Newest to oldest</option>  
                    </select>
                </div>
            </div>
        </div>
    )
}
