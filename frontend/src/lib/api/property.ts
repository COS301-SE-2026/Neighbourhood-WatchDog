import { CreatePropertyReq, CreatePropertyRes, InvitePropertyMemberInput, InvitePropertyMemberResponse, PropertyMembers, PropertyRes } from '@/lib/validators/property'
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
  return apiCall<PropertyDetailedRes>(
    `/properties/${propertyId}`, 
    {method: 'GET'},
  )
}

export async function getPropertyMembers(propertyId: string):Promise<PropertyMembers> {
  return apiCall<PropertyMembers>(`/properties/${propertyId}/members`, {
    method: "GET"
  })
}

export async function invitePropertyMember(
  propertyId: string, data: InvitePropertyMemberInput
): Promise<InvitePropertyMemberResponse> {
  return apiCall<InvitePropertyMemberResponse>(
    `/properties/${propertyId}/member`,
    {
      method: "POST",
      body: data
    }
  );
}

export async function removePropertyMember(
  propertyId: string,
  userId: string
): Promise<void> {
  await apiCall<void>(`/properties/${propertyId}/members/${userId}`, {
    method: "DELETE"
  });
  
}
