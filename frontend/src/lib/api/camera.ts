import { CameraInput, Camera } from '@/lib/validators/camera'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface RegisterCameraRes {
  status: number
  message?: string
  data?: Camera
}

export async function addCamera(data: CameraInput): Promise<Camera> {
  const response = await fetch(`${API_BASE}/cameras`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error('Failed to add camera')
  const result: RegisterCameraRes = await response.json()
  if (!result.data) throw new Error(result.message || 'No data returned')
  return result.data
}

export async function deleteCamera(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/cameras/${id}`, { method: 'DELETE' })
  if (!response.ok) throw new Error('Failed to delete camera')
}