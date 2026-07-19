import { CameraInput, Camera, CameraEditInput } from '@/lib/validators/camera'
import { apiCall } from './client'

interface RegisterCameraRes {
  status: number
  message?: string
  data?: Camera
}

interface EditCameraRes {
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

export async function editCamera(id: string, data: CameraEditInput): Promise<Camera> {
  const result = await apiCall<EditCameraRes>(`/camera/${id}`, {
    method: "PATCH",
    body: data,
  })
  if (!result.data) throw new Error(result.message || 'No data returned')
  return result.data
}