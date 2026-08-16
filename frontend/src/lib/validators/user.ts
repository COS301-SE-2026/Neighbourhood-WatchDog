import { z } from "zod"

export const SystemRoleEnumSchema = z.enum([
  "SYSTEM_ADMIN",
  "RESIDENT",
  "SECURITY_OFFICER",
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
    neighbourhood_id: z.string().nullable(),
    is_admin: z.boolean(),
});

export const CurrentUserContextResSchema = z.object({
    user: CurrentUserSummarySchema,
    neighbourhoods: z.array(CurrentUserNeighbourhoodSchema ),
    properties: z.array(CurrentUserPropertySchema),
});

export type CurrentUserSummary = z.infer<typeof CurrentUserSummarySchema>
export type CurrentUserNeighbourhood = z.infer<typeof CurrentUserNeighbourhoodSchema>
export type CurrentUserProperty = z.infer<typeof CurrentUserPropertySchema>
export type CurrentUserContextRes = z.infer<typeof CurrentUserContextResSchema>