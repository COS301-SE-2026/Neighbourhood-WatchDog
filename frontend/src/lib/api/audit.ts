import { GetAuditLogRes, getAuditLogsResSchema, PaginatedResponse, AuditLog } from '../validators/audit'
import { apiCall } from './client'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export type AuditLogsFilters = {
  searchTerm?: string
  action?: 'UPDATE' | 'DELETE' | 'CREATE'
  // note that the dates are stored as strings 
  // to avoid unnecessary conversion errors 
  // since the dates are never actually used 
  // as dates on the frontend
  startDate?: string 
  endDate?: string 
  sortOrder?: 'ASC' | 'DESC'
}

export async function getAuditLogs(page: number, size: number, filters?: AuditLogsFilters): Promise<PaginatedResponse<AuditLog>> {
  console.log() //TODO: remove this

  let url = `/audit/get-audit-logs?page=${page}&size=${size}`

  if (filters?.searchTerm)
    url += `&search_term=${filters.searchTerm}`

  if (filters?.action)
    url += `&action=${filters.action}`

  if (filters?.startDate)
    url += `&start_date=${filters.startDate}`

  if (filters?.endDate)
    url += `&end_date=${filters.endDate}`

  if (filters?.sortOrder)
    url += `&sort_order=${filters.sortOrder}`

  const result = await apiCall<GetAuditLogRes>(url, {
    method: 'GET',
  })
  if (!result.data) 
    throw new Error(result.message || 'No data returned')
  
  const parsedObject = getAuditLogsResSchema.parse(result)
  return parsedObject.data
}