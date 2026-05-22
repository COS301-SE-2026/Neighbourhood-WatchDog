import { apiCall } from "@/lib/api/client";
import { useState, useEffect } from "react";

export interface Property {
  property_id: string
  address: string
  neighbourhood_id: string | null
  property_type: string
  created_at: string
}

//function to get the properties when page loads
export function useProperties() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [properties, setProperties] = useState<Property[]>([])

  useEffect(() =>{
    const fetchProperties = async () => {
      try {
        setLoading(true)
        const response = await apiCall('/properties/my-properties', {method: 'GET'}) as Property[]
        setProperties(response)
        setError(null)
      } catch(err) {
        setError(err instanceof Error? err.message : 'Failed to fetch properties')
        setProperties([])
      } finally {
        setLoading(false)
      }
    }

    fetchProperties()
  }, [])

  const addProperty = (property: Property) => {
    setProperties([...properties, property])
  }

  return { properties, loading, error, addProperty }
}