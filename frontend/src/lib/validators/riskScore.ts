import { z } from "zod";

export const RiskLevel = z.enum(["LOW", "MEDIUM", "HIGH"]);

export const Granularities = z.enum(["minute", "hour", "day", "week"]);

export const RiskScoreRes = z.object({
  neighbourhood_id: z.uuid(),
  score: z.number(),
  classification: RiskLevel,
  alert_count: z.number().int(),
  calculated_at: z.iso.datetime(),
});

export const NeighbourhoodRiskScoreRes = z.object({
  status: z.number().int(),
  message: z.string(),
  data: RiskScoreRes.nullable().optional(),
});

export const NeighbourhoodRiskScoreHistory = z.object({
  status: z.number().int(),
  message: z.string(),
  data: RiskScoreRes.array(),
});

export type RiskLevel = z.infer<typeof RiskLevel>;
export type Granularities = z.infer<typeof Granularities>;
export type RiskScoreRes = z.infer<typeof RiskScoreRes>;
export type NeighbourhoodRiskScoreRes = z.infer<
  typeof NeighbourhoodRiskScoreRes
>;
export type NeighbourhoodRiskScoreHistory = z.infer<
  typeof NeighbourhoodRiskScoreHistory
>;
