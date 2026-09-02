import { apiCall } from './client'
import { CreateNeighbourhoodReq, NeighbourhoodRes, CreateNeighbourhoodRes, NeighbourPropertiesRes, UpdateMemberRoleReq, NeighbourhoodMemberRes, UpdateMemberRoleRes, NeighbourhoodMembersRes } from '../validators/neighbourhood'

export async function addNeighbourhood(data: CreateNeighbourhoodReq): Promise<NeighbourhoodRes> {
  const result = await apiCall<CreateNeighbourhoodRes>('/neighbourhood/create-neighbourhood', {
    method: 'POST',
    body: data,
  })
  if (!result.data) throw new Error(result.message || 'No data returned')
  return result.data
}

export async function getNeighbourhoods(): Promise<NeighbourhoodRes[]> {
  return apiCall<NeighbourhoodRes[]>('/neighbourhood/list', {
    method: 'GET',
  })
}

export async function getNeighbourhood(id: string): Promise<NeighbourhoodRes> {
  return apiCall<NeighbourhoodRes>(`/neighbourhood/${id}`, {
    method: 'GET',
  })
}

export async function joinNeighbourhood(joinCode: string): Promise<NeighbourhoodRes> {
  return apiCall<NeighbourhoodRes>('/neighbourhood/join', {
    method: 'POST',
    body: { join_code: joinCode },
  })
}

export async function getNeighbourhoodPropertyDetails(): Promise<NeighbourPropertiesRes> {
  return apiCall<NeighbourPropertiesRes>(
    `/neighbourhood/properties`, 
    {method: 'GET'},
  )
}


export async function getNeighbourhoodMembers(
  neighbourhoodId: string,
): Promise<NeighbourhoodMembersRes> {
  return apiCall<NeighbourhoodMemberRes[]>(
    `/neighbourhood/${neighbourhoodId}/members`,
    {
      method: "GET",
    },
  );
}


export async function updateNeighbourhoodMemberRole(
  neighbourhoodId: string,
  memberUserId: string,
  data: UpdateMemberRoleReq,
): Promise<NeighbourhoodMemberRes> {
  const result = await apiCall<UpdateMemberRoleRes>(
    `/neighbourhood/${neighbourhoodId}/members/${memberUserId}/role`,
    {
      method: "PATCH",
      body: data,
    },
  );

  if (!result.data) {
    throw new Error(result.message || "No member data returned");
  }

  return result.data;
}