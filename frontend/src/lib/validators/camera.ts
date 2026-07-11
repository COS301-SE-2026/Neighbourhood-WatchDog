import { z } from 'zod'

//make sure these correspond to the backend schema and whatnot
export const cameraInputSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  rtsp_url: z.string().min(1, 'RTSP URL is required').pipe(z.url({ error: 'Must be valid RTSP URL' })),
  location: z.string().min(1, 'Location is required'),
  visibility: z.enum(['PUBLIC', 'PRIVATE', 'NEIGHBOURHOOD']),
  enabled: z.boolean(),
  property_id: z.uuid('Invalid property ID'),
})

export const cameraSchema = z.object({
  id: z.uuid(),
  property_id: z.uuid(),
  neighbourhood_id: z.uuid(),
  name: z.string(),
  visibility: z.enum(['PUBLIC', 'PRIVATE', 'NEIGHBOURHOOD']),
  location: z.string(),
  rtsp_url: z.string(),
  enabled: z.boolean(),
  created_at: z.iso.datetime(),
})

export const cameraEditSchema = z.object({
  name: z.string().min(1, 'Camera is required').optional(),
  location: z.string().min(1, 'Location is required').optional(),
  visibility: z.enum(['PUBLIC', 'PRIVATE', 'NEIGHBOURHOOD']).optional(),
  enabled: z.boolean().optional()
})

export type Camera = z.infer<typeof cameraSchema>
export type CameraInput = z.infer<typeof cameraInputSchema>
export type CameraEditInput = z.infer<typeof cameraEditSchema>
