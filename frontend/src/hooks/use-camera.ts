import { addCamera as apiAddCamera, deleteCamera as apiDeleteCamera, fetchCameras as apiFetchCameras } from "@/lib/api/camera"
import { useState, useCallback, useEffect } from "react"
import { Camera, CameraInput } from "@/lib/validators/camera"

export function useCameras(propertyId: string, initialCameras: Camera[] = []) {
  const [cameras, setCameras] = useState(initialCameras)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!propertyId) return

    const loadCameras = async () => {
      setLoading(true)
      setError(null)
      try {
        const fetchedCameras = await apiFetchCameras(propertyId)
        setCameras(fetchedCameras)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load cameras'
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    void loadCameras()
  }, [propertyId])

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