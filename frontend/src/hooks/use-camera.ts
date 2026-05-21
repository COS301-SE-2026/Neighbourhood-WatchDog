import { addCamera as apiAddCamera, deleteCamera as apiDeleteCamera } from "@/lib/api/camera"
import { useState, useCallback } from "react"
import { Camera, CameraInput } from "@/lib/validators/camera"

export function useCameras(initialCameras: Camera[] = []) {
  const [cameras, setCameras] = useState(initialCameras)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addCamera = useCallback(async (data: CameraInput) => {
    setLoading(true)
    setError(null)
    try {
      const newCamera = await apiAddCamera(data)
      setCameras(prev => [...prev, newCamera])
      return newCamera
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to add camera'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const deleteCamera = useCallback(async (id: string) => {
    setLoading(true)
    setError(null)
    try {
      await apiDeleteCamera(id)
      setCameras(prev => prev.filter(c => c.id !== id))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete camera'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return { cameras, addCamera, deleteCamera, loading, error }
}
