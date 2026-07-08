import { GetAuditLogRes, PaginatedResponse, AuditLog } from '../validators/audit'
import { apiCall } from './client'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function getAuditLogs(page: number, size: number): Promise<PaginatedResponse<AuditLog>> {
    console.log() //TODO: remove this

    const result = await apiCall<GetAuditLogRes>(`/audit/get-audit-logs?page=${page}&size=${size}`, {
        method: 'GET',
    })
    if (!result.data) 
        throw new Error(result.message || 'No data returned')
    
    return result.data
}