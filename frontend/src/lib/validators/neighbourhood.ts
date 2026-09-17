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

export const NeighbourhoodMemberResSchema = z.object({
  user_id: z.string().uuid(),
  first_name: z.string(),
  last_name: z.string(),
  email: z.string().email(),
  role: z.enum([
    "RESIDENT",
    "SECURITY_OFFICER",
    "NEIGHBOURHOOD_ADMIN"
  ])
});

export const NeighbourhoodMembersResSchema = z.array(NeighbourhoodMemberResSchema);

export const UpdateMemberRoleReqSchema = z.object({
  role: z.enum([
    "RESIDENT",
    "SECURITY_OFFICER",
    "NEIGHBOURHOOD_ADMIN"
  ])
});

export const UpdateMemberRoleResSchema = z.object({
  status: z.number().int(),
  message: z.string(),
  data: NeighbourhoodMemberResSchema
});

export const LeaveNeighbourhoodParamsSchema = z.object({
  neighbourhoodId: z.uuid("Invalid neighbourhood ID"),
  propertyId: z.uuid("Invalid property ID")
});

export const AvailabilityStatusSchema = z.enum(["AVAILABLE", "BUSY", "UNAVAILABLE"]);

export const UpdateSecurityAvailabilityReqSchema = z.object({
  neighbourhood_id: z.uuid("Invalid neighbourhood ID"),
  new_availability: AvailabilityStatusSchema,
});

export const UpdateSecurityAvailabilityResSchema = z.object({
  status: z.number().int(),
  message: z.string().nullable().optional(),
});

export const GetSecurityAvailabilityResSchema = z.object({
  status: z.number().int(),
  message: z.string().nullable().optional(),
  availability: AvailabilityStatusSchema,
  location_updated_at: z.coerce.date(),
});

export const UpdateSecurityLocationReqSchema = z.object({
  neighbourhood_id: z.uuid("Invalid neighbourhood ID"),
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
});

export const UpdateSecurityLocationResSchema = z.object({
  status: z.number().int(),
  message: z.string().nullable().optional(),
});

export const OfficerLocationResSchema = z.object({
  officer_id: z.uuid("Invalid officer ID"),
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  location_updated_at: z.coerce.date(),
  is_stale: z.boolean(),
});

export type CreateNeighbourhoodReq = z.infer<typeof CreateNeighbourhoodReqSchema>;
export type NeighbourhoodRes = z.infer<typeof NeighbourhoodResSchema>;
export type CreateNeighbourhoodRes = z.infer<typeof CreateNeighbourhoodResSchema>;
export type NeighbourPropertiesRes = z.infer<typeof NeighbourPropertiesResSchema>;
export type NeighbourhoodMemberRes = z.infer<typeof NeighbourhoodMemberResSchema>;
export type NeighbourhoodMembersRes = z.infer<typeof NeighbourhoodMembersResSchema>;
export type UpdateMemberRoleReq = z.infer<typeof UpdateMemberRoleReqSchema>;
export type UpdateMemberRoleRes = z.infer<typeof UpdateMemberRoleResSchema>;
export type LeaveNeighbourhoodParams = z.infer<typeof LeaveNeighbourhoodParamsSchema>;
export type AvailabilityStatus = z.infer<typeof AvailabilityStatusSchema>;
export type UpdateSecurityAvailabilityReq = z.infer<typeof UpdateSecurityAvailabilityReqSchema>;
export type UpdateSecurityAvailabilityRes = z.infer<typeof UpdateSecurityAvailabilityResSchema>;
export type GetSecurityAvailabilityRes = z.infer<typeof GetSecurityAvailabilityResSchema>;
export type UpdateSecurityLocationRes = z.infer<typeof UpdateSecurityLocationResSchema>;
export type UpdateSecurityLocationReq = z.infer<typeof UpdateSecurityLocationReqSchema>;
export type OfficerLocationRes = z.infer<typeof OfficerLocationResSchema>;
