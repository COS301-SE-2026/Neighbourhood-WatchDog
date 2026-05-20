import {z } from "zod"

export const PropertyTypeEnum = z.enum([
  "PRIVATE",
  "PUBLIC",
]);

export const CreatePropertyReqSchema = z.object({
  address: z.string().min(1),
  property_type: PropertyTypeEnum,
});

export const PropertyResSchema = z.object({
  user_id: z.uuid(),
  neighbourhood_id: z.uuid().nullable(),
  address: z.string().min(1),
  property_type: z.string().min(1),
  created_at: z.coerce.date(),
});

export const CreatePropertyResSchema = z.object({
  status: z.number().int(),
  message: z.string().nullable().optional(),
  data: PropertyResSchema.nullable().optional(),
});

// Types
export type CreatePropertyReq = z.infer<typeof CreatePropertyReqSchema>;
export type PropertyRes = z.infer<typeof PropertyResSchema>;
export type CreatePropertyRes = z.infer<typeof CreatePropertyResSchema>;
export type PropertyType = z.infer<typeof PropertyTypeEnum>;