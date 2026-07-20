import { CreatePropertyReq, CreatePropertyRes, PropertyRes } from '@/lib/validators/property'
import { PropertyDetailedRes } from '@/lib/validators/property'
import { apiCall } from './client'

export async function addProperty(data: CreatePropertyReq): Promise<PropertyRes> {
  
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
