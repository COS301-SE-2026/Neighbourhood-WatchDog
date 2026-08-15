import { z } from "zod"

export const SystemRoleEnum = z.enum([
  "SYSTEM_ADMIN",
  "RESIDENT",
  "SECURITY_OFFICER",
]);

export const CurrentUserSummary= z.object({

    id: z.string(),
    name: z.string(),
    system_role: SystemRoleEnum,
});

export const CurrentUserNeighbourhood = z.object({

    id: z.string(),
    name: z.string(),
    role: SystemRoleEnum,
});

export const CurrentUserProperty = z.object({

    id: z.string(),
    address: z.string(),
    neighbourhoodId: z.string() || z.string().nullable(),
    is_admin: z.boolean(),
});

export const CurrentUserContextRes = z.object({
    user: CurrentUserSummary,
    neighbourhoods: z.array(CurrentUserNeighbourhood),
    properties: z.array(CurrentUserProperty),
});