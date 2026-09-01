import { z } from "zod"

export const SystemRoleEnumSchema = z.enum([
  "SYSTEM_ADMIN",
  "RESIDENT",
  "SECURITY_OFFICER",
  "NEIGHBOURHOOD_ADMIN"
]);

export const CurrentUserSummarySchema = z.object({

    id: z.string(),
    name: z.string(),
    system_role: SystemRoleEnumSchema ,
});

export const CurrentUserNeighbourhoodSchema  = z.object({

    id: z.string(),
    name: z.string(),
    role: SystemRoleEnumSchema,
});

export const CurrentUserPropertySchema  = z.object({

    id: z.string(),
    address: z.string(),
    neighbourhood: CurrentUserNeighbourhoodSchema.nullable(),
    is_admin: z.boolean(),
});

export const CurrentUserContextResSchema = z.object({
    user: CurrentUserSummarySchema,
    properties: z.array(CurrentUserPropertySchema),
});

export const UserSettingsResSchema = z.object({
  first_name: z.string().nullable(),
  last_name: z.string().nullable(),
  email: z.email(),
  phone_number: z.string().nullable(),
  system_role: SystemRoleEnumSchema,
});

export const UpdateUserSettingsPayloadSchema = z.object({
  first_name: z.string(),
  last_name: z.string(),
  phone_number: z.string().nullable(),
});

export type CurrentUserSummary = z.infer<typeof CurrentUserSummarySchema>
export type CurrentUserNeighbourhood = z.infer<typeof CurrentUserNeighbourhoodSchema>
export type CurrentUserProperty = z.infer<typeof CurrentUserPropertySchema>
export type CurrentUserContextRes = z.infer<typeof CurrentUserContextResSchema>
export type UserSettingsRes = z.infer<typeof UserSettingsResSchema>;
export type UpdateUserSettingsPayload = z.infer<typeof UpdateUserSettingsPayloadSchema>;