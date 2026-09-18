import { apiCall } from './client'
import { 
  CreateNeighbourhoodReq, 
  NeighbourhoodRes, 
  CreateNeighbourhoodRes, 
  NeighbourPropertiesRes,
  UpdateMemberRoleReq, 
  NeighbourhoodMemberRes, 
  UpdateMemberRoleRes, 
  NeighbourhoodMembersRes, 
  LeaveNeighbourhoodParams, 
  LeaveNeighbourhoodParamsSchema,  
  UpdateSecurityAvailabilityRes,
  GetSecurityAvailabilityRes,
  UpdateSecurityLocationReq,
  UpdateSecurityLocationRes,
  DutyStatus,
} from '../validators/neighbourhood'

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

export async function leaveNeighbourhood(
  params: LeaveNeighbourhoodParams
): Promise<void> {
  const { neighbourhoodId, propertyId } = LeaveNeighbourhoodParamsSchema.parse(params);

  await apiCall<void>(
    `/neighbourhood/${neighbourhoodId}/properties/${propertyId}/leave`,
    {
      method: "PATCH"
    }
  );
}

export async function updateSecurityAvailability(
  neighbourhoodId: string,
  newAvailability: DutyStatus,
): Promise<UpdateSecurityAvailabilityRes> {
  return apiCall<UpdateSecurityAvailabilityRes>(
    `/neighbourhood/security/availability`,
    {
      method: "PATCH",
      body: {
        neighbourhood_id: neighbourhoodId,
        new_availability: newAvailability,
      },
    },
  );
}

export async function updateSecurityLocation(
  req: UpdateSecurityLocationReq,
): Promise<UpdateSecurityLocationRes> {
  return apiCall<UpdateSecurityLocationRes>(
    `/neighbourhood/security/update-location`,
    {
      method: "PATCH",
      body: {
        neighbourhood_id: req.neighbourhood_id,
        latitude: req.latitude,
        longitude: req.longitude,
      },
    },
  );
}

export async function getSecurityAvailability(
  neighbourhoodId: string,
): Promise<GetSecurityAvailabilityRes> {
  return apiCall<GetSecurityAvailabilityRes>(
    `/neighbourhood/${neighbourhoodId}/security/availability`,
    { method: "GET", },
  );
}