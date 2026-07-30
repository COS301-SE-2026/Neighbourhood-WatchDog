import { z } from "zod";

export const CreateNeighbourhoodReqSchema = z.object({
  name: z.string().min(1, "Name is required"),
  location: z.string().min(1, "Location is required"),
  property_id: z.string().regex(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i, "Invalid UUID format"),
});

export const NeighbourhoodResSchema = z.object({
  id: z.string().regex(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i, "Invalid UUID format"),
  name: z.string().min(1),
  location: z.string().min(1),
  join_code: z.string().min(1),
  created_at: z.coerce.date(),
});

export const CreateNeighbourhoodResSchema = z.object({
  status: z.number().int(),
  message: z.string().nullable().optional(),
  data: NeighbourhoodResSchema.nullable().optional(),
});

export const NeighbourPropertychema = z.object({
  id: z.string(),
  address: z.string(),
  property_type: z.enum(["PUBLIC", "PRIVATE"]),
  neighbourhood_id: z.string().nullable(),
  neighbourhood_name: z.string().optional(),
})

export const NeighbourPropertiesResSchema = z.array(NeighbourPropertychema)

export type CreateNeighbourhoodReq = z.infer<typeof CreateNeighbourhoodReqSchema>;
export type NeighbourhoodRes = z.infer<typeof NeighbourhoodResSchema>;
export type CreateNeighbourhoodRes = z.infer<typeof CreateNeighbourhoodResSchema>;
export type NeighbourPropertiesRes = z.infer<typeof NeighbourPropertiesResSchema>;
