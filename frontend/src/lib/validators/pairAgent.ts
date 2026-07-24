import {z} from "zod";

const uuidSchema = z
    .string()
    .regex(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i, "Neighbourhood ID must be a valid UUID")

export const LinkPropertyTokenSchema = z.object({
    token: z.string(),
    expires_at: z.coerce.date(),
})

export const LinkPropertyTokenResSchema = z.object({
    status: z.number(),
    message: z.string().nullable().optional(),
    data: LinkPropertyTokenSchema.nullable().optional(),
})

export const EdgeAgentsCredentialsSchema = z.object({
    property_id: uuidSchema,
    address: z.string(),
    api_key: z.string(),
    created_at: z.coerce.date(),
})

export const EdgeAgentsCredentialsResSchema = z.object({
    status: z.number(),
    message: z.string().nullable().optional(),
    data: EdgeAgentsCredentialsSchema.nullable().optional(),
})

export type LinkPropertyToken = z.infer<typeof LinkPropertyTokenSchema>
export type LinkPropertyTokenRes = z.infer<typeof LinkPropertyTokenResSchema>
export type EdgeAgentsCredentials = z.infer<typeof EdgeAgentsCredentialsSchema>
export type EdgeAgentsCredentialsRes = z.infer<typeof EdgeAgentsCredentialsResSchema>