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
        <div className="flex flex-col gap-2">
            <input
                className="border-1 rounded-radius-lg"
                type="text"
                onChange={(e) => setRawSearch(e.target.value)} 
                placeholder="Search by ID, Action, Target Entity Type or Target Entity ID field..."
            />
            <div className="flex flex-row justify-between">
                <select
                    name="actions"
                    // value={action}
                    onChange={(e) => onChange({...filters, action: e.target.value as AuditLogsFilters['action']})}>
                    <option value="UPDATE">UPDATE</option>
                    <option value="CREATE">CREATE</option>
                    <option value="DELETE">DELETE</option>
                </select>
                <div>
                    <label>From:</label>
                    <input  
                        type="datetime-local"
                        onChange={(e) => onChange({...filters, startDate: e.target.value})}
                    ></input>
                </div>
                <div>
                    <label>Up To:</label>
                    <input
                        type="datetime-local"
                        onChange={(e) => onChange({...filters, endDate: e.target.value})}
                    ></input>
                </div>
                <select
                    name="sortOrder"
                    // value={sortOrder}
                    onChange={(e) => onChange({...filters, sortOrder: e.target.value as AuditLogsFilters['sortOrder']})}>  
                    <option value="ASC">Oldest to newest</option>
                    <option value="DESC">Newest to oldest</option>  
                </select>
            </div>
        </div>
    )
}