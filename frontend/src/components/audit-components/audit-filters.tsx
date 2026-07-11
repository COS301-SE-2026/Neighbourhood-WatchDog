"use client"

import { useEffect, useState } from "react"
import { AuditLogsFilters } from "@/lib/api/audit"
import { useDebounce } from "@/hooks/use-debounce"

// user should be able to filter by:
//  search
//  start date 
//  end date
//  action
//  target entity type

interface AuditFiltersProps{
    onChange: (filters: AuditLogsFilters) => void
}

export function AuditFilters({
    onChange
}: AuditFiltersProps){
    const [searchTerm, setSearchTerm] = useState<AuditLogsFilters['searchTerm']>()
    const debouncedSearch = useDebounce(searchTerm)
    const [action, setAction] = useState<AuditLogsFilters['action']>()
    const [startDate, setStartDate] = useState<AuditLogsFilters['startDate']>()
    const [endDate, setEndDate] = useState<AuditLogsFilters['endDate']>()
    const [sortOrder, setSortOrder] = useState<AuditLogsFilters['sortOrder']>()


    useEffect(() => {
        onChange({searchTerm: debouncedSearch, action, startDate, endDate, sortOrder})
    }, [debouncedSearch, action, startDate, endDate, sortOrder])

    return (
        <div className="flex flex-col gap-2">
            <input
                type="text"
                onChange={(e) => setSearchTerm(e.target.value)} 
                placeholder="Search by any field..."
            />
            <select
                name="actions"
                // value={action}
                onChange={(e) => setAction(e.target.value as AuditLogsFilters['action'])
                }>
                <option value="UPDATE">UPDATE</option>
                <option value="CREATE">CREATE</option>
                <option value="DELETE">DELETE</option>
            </select>
            <label>Choose a start date:</label>
            <input  
                type="datetime-local"
                onChange={(e) => setStartDate(e.target.value)}
            ></input>
            <label>Choose an end date:</label>
            <input
                type="datetime-local"
                onChange={(e) => setEndDate(e.target.value)}
            ></input>
            <select
                name="sortOrder"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as AuditLogsFilters['sortOrder'])}>    
            </select>
        </div>
    )
}