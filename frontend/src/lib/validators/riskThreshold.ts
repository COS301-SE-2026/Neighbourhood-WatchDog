import { z } from "zod";

export const UpdateRiskThresholdConfigReq = z.object({
  low_max: z.number().nullable().optional(),
  medium_max: z.number().nullable().optional(),
});

export const RiskThresholdConfigRes = z.object({
  id: z.uuid(),
  neighbourhood_id: z.uuid().nullable(),
  low_max: z.number(),
  medium_max: z.number(),
  updated_at: z.iso.datetime(),
});

export const NeighbourhoodRiskThresholdConfigRes = z.object({
  status: z.number().int(),
  message: z.string(),
  data: RiskThresholdConfigRes,
});

export type UpdateRiskThresholdConfigReq = z.infer<
  typeof UpdateRiskThresholdConfigReq
>;

export type RiskThresholdConfigRes = z.infer<
  typeof RiskThresholdConfigRes
>;

export type NeighbourhoodRiskThresholdConfigRes = z.infer<
  typeof NeighbourhoodRiskThresholdConfigRes
>;
