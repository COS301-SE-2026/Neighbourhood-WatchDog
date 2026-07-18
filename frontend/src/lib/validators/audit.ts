import { z } from "zod"

export const AuditActionEnum = z.enum([
    "CREATE",
    "UPDATE",
    "DELETE",
])

export const paginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) => 
    z.object({
        total: z.number().int(),
        page: z.number().int(),
        size: z.number().int(),
        results: z.array(itemSchema)
    })


export const auditLogSchema = z.object({
    id: z.string().regex(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i, "Invalid UUID format"),
    user_id: z.string().regex(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i, "Invalid UUID format"),
    action: AuditActionEnum,
    target_entity_type: z.string().min(1).nullable().optional(),
    target_entity_id: z.string().regex(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i, "Invalid UUID format").nullable().optional(),
    timestamp: z.coerce.date(),
    old_values: z.record(z.string(), z.any()).nullable().optional(),
    new_values: z.record(z.string(), z.any()).nullable().optional(),
})

export const getAuditLogsResSchema = z.object({
    status: z.number().int(),
    message: z.string().nullable().optional(),
    data: paginatedResponseSchema(auditLogSchema),
})

export type GetAuditLogRes = z.infer<typeof getAuditLogsResSchema>
export type PaginatedResponse<T> = z.infer<ReturnType<typeof paginatedResponseSchema<z.ZodType<T>>>>
export type AuditAction = z.infer<typeof AuditActionEnum>
export type AuditLog = z.infer<typeof auditLogSchema>
