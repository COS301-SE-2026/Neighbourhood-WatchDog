import { z } from 'zod'

//make sure these correspond to the backend schema and whatnot
export const cameraInputSchema = z.object({
  rtsp_url: z.string().min(1, 'RTSP URL is required').pipe(z.url({ error: 'Must be valid RTSP URL' })),
  location: z.string().min(1, 'Location is required'),
  visibility: z.enum(['PUBLIC', 'PRIVATE']),
  property_id: z.uuid('Invalid property ID'),
})

export const cameraSchema = z.object({
  id: z.uuid(),
  property_id: z.uuid(),
  neighbourhood_id: z.uuid(),
  visibility: z.enum(['public', 'private', 'neighbourhood']),
  location: z.string(),
  rtsp_url: z.string(),
  created_at: z.iso.datetime(),
})

export type Camera = z.infer<typeof cameraSchema>
export type CameraInput = z.infer<typeof cameraInputSchema>
