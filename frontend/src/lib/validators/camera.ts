import { z } from "zod";
import {
  cameraCoverageSchema,
  MAX_CAMERA_COVERAGE_RANGE_METRES,
} from "./camera-coverage";

export const cameraInputSchema = z.object({
  name: z.string().min(1, "Name is required"),
  rtsp_url: z
    .string()
    .min(1, "RTSP URL is required")
    .pipe(z.url({ error: "Must be a valid RTSP URL" })),
  location: z.string().min(1, "Location is required"),
  visibility: z.enum(["PUBLIC", "PRIVATE", "NEIGHBOURHOOD"]),
  property_id: z.uuid("Invalid property ID"),
  coverage: cameraCoverageSchema.optional(),
});

export const cameraSchema = z.object({
  id: z.uuid(),
  property_id: z.uuid(),
  neighbourhood_id: z.uuid(),
  name: z.string(),
  visibility: z.enum(["PUBLIC", "PRIVATE", "NEIGHBOURHOOD"]),
  location: z.string(),
  enabled: z.boolean(),
  created_at: z.iso.datetime(),
});

export const cameraEditSchema = z.object({
  name: z.string().min(1, "Camera is required").optional(),
  location: z.string().min(1, "Location is required").optional(),
  visibility: z
    .enum(["PUBLIC", "PRIVATE", "NEIGHBOURHOOD"])
    .optional(),
  enabled: z.boolean().optional(),
});

export type Camera = z.infer<typeof cameraSchema>;
export type CameraInput = z.infer<typeof cameraInputSchema>;
export type CameraEditInput = z.infer<typeof cameraEditSchema>;
export type CameraCoverage = z.infer<typeof cameraCoverageSchema>;

export { MAX_CAMERA_COVERAGE_RANGE_METRES };