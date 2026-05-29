import { CreatePropertyReq, CreatePropertyRes, PropertyRes } from '@/lib/validators/property'
import { PropertyDetailedRes } from '@/lib/validators/property'
import { apiCall } from './client'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function addProperty(data: CreatePropertyReq): Promise<PropertyRes> {
  console.log(data)
  
  const result = await apiCall<CreatePropertyRes>('/properties/create-property', {
    method: 'POST',
    body: data,
  })
  if (!result.data) throw new Error(result.message || 'No data returned')
  return result.data
}

export async function getPropertyDetails(propertyId: string): Promise<PropertyDetailedRes> {
  return apiCall<PropertyDetailedRes>(`/properties/${propertyId}`, {
    method: 'GET',
  })
}
