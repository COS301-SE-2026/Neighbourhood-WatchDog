import { z } from "zod";

export const CreateNeighbourhoodReqSchema = z.object({
  name: z.string().min(1, "Name is required"),
  location: z.string().min(1, "Location is required"),
  property_id: z.uuid(),
});

export const NeighbourhoodResSchema = z.object({
  id: z.uuid(),
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

export type CreateNeighbourhoodReq = z.infer<typeof CreateNeighbourhoodReqSchema>;
export type NeighbourhoodRes = z.infer<typeof NeighbourhoodResSchema>;
export type CreateNeighbourhoodRes = z.infer<typeof CreateNeighbourhoodResSchema>;
