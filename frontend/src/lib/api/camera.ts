import { CameraInput, Camera } from '@/lib/validators/camera'
import { apiCall } from './client'

interface RegisterCameraRes {
  status: number
  message?: string
  data?: Camera
}

interface CamerasRes {
  status: number
  message?: string
  data?: Camera[]
}

export async function addCamera(data: CameraInput): Promise<Camera> {
  const result = await apiCall<RegisterCameraRes>('/camera/register-camera', {
    method: 'POST',
    body: data,
  })
  if (!result.data) throw new Error(result.message || 'No data returned')
  return result.data
}

export async function fetchCameras(propertyId: string): Promise<Camera[]> {
  const result = await apiCall<CamerasRes>(`/camera/property/${propertyId}`)
  return result.data || []
}

export async function deleteCamera(id: string): Promise<void> {
  await apiCall(`/camera/${id}`, { method: 'DELETE' })
}