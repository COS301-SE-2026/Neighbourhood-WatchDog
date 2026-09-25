import { z } from "zod";

export const MAX_CAMERA_ORIGIN_DISTANCE_METRES = 100;
export const MAX_CAMERA_COVERAGE_RANGE_METRES = 200;

export const cameraCoverageSchema = z.object({
  origin_latitude: z.number().finite().min(-90).max(90),
  origin_longitude: z.number().finite().min(-180).max(180),
  coverage_bearing_degrees: z.number().finite().min(0).lt(360),
  coverage_angle_degrees: z.number().finite().min(1).max(180),
  coverage_range_metres: z
    .number()
    .finite()
    .min(1)
    .max(MAX_CAMERA_COVERAGE_RANGE_METRES),
});

export type CameraCoverageInput = z.infer<typeof cameraCoverageSchema>;