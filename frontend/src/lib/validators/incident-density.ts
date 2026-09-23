import { z } from "zod";

const DateOnlySchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/);

export const IncidentDensityCellSchema = z.object({
  cell_id: z.string().min(1),
  grid_x: z.number(),
  grid_y: z.number(),
  latitude: z.number(),
  longitude: z.number(),
  incident_count: z.number().int().nonnegative(),
});

export const IncidentDensityDataSchema = z.object({
  neighbourhood_id: z.string().min(1),
  start_date: DateOnlySchema,
  end_date: DateOnlySchema,
  cell_size_metres: z.number().int().positive(),
  min_count: z.number().int().nonnegative(),
  max_count: z.number().int().nonnegative(),
  cells: z.array(IncidentDensityCellSchema),
});

export const IncidentDensityResponseSchema = z.object({
  status: z.number().int(),
  message: z.string().nullable(),
  data: IncidentDensityDataSchema,
});

export type IncidentDensityCell = z.infer<typeof IncidentDensityCellSchema>;

export type IncidentDensityData = z.infer<typeof IncidentDensityDataSchema>;

export interface IncidentDensityViewport {
  west: number;
  south: number;
  east: number;
  north: number;
}
