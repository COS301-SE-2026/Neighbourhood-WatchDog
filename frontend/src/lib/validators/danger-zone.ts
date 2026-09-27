import { z } from "zod";

const DateOnlySchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/);

const ScoreSchema = z
  .number()
  .finite()
  .min(0)
  .max(1);

export const DangerZoneCellSchema = z.object({
  cell_id: z.string().min(1),
  grid_x: z.number().int(),
  grid_y: z.number().int(),

  latitude: z.number().finite().min(-90).max(90),
  longitude: z.number().finite().min(-180).max(180),

  south: z.number().finite().min(-90).max(90),
  west: z.number().finite().min(-180).max(180),
  north: z.number().finite().min(-90).max(90),
  east: z.number().finite().min(-180).max(180),

  incident_count: z
    .number()
    .int()
    .nonnegative(),

  incident_score: ScoreSchema,
  coverage_ratio: ScoreSchema,
  coverage_sparsity: ScoreSchema,
  danger_score: ScoreSchema,
});

export const DangerZoneDataSchema = z.object({
  neighbourhood_id: z.string().uuid(),
  window_start: DateOnlySchema.nullable(),
  window_end: DateOnlySchema.nullable(),

  calculated_at: z
    .string()
    .datetime({
      offset: true,
    })
    .nullable(),

  cell_size_metres: z
    .number()
    .int()
    .positive(),

  min_score: ScoreSchema,
  max_score: ScoreSchema,

  cells: z.array(DangerZoneCellSchema),
});

export const DangerZoneResponseSchema =
  z.object({
    status: z.number().int(),
    message: z.string().nullable().optional(),
    data: DangerZoneDataSchema,
  });

export type DangerZoneCell = z.infer<
  typeof DangerZoneCellSchema
>;

export type DangerZoneData = z.infer<
  typeof DangerZoneDataSchema
>;

export interface DangerZoneViewport {
  west: number;
  south: number;
  east: number;
  north: number;
}