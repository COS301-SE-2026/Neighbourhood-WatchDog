import { z } from "zod";

export const JoinCodeResSchema = z.object({
  join_code: z.string().min(1, "Name is required")
});

export type JoinCodeRes = z.infer<typeof JoinCodeResSchema>;