import { apiCall } from './client'
import { CreateNeighbourhoodReq, NeighbourhoodRes, CreateNeighbourhoodRes } from '../validators/neighbourhood'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function addNeighbourhood(data: CreateNeighbourhoodReq): Promise<NeighbourhoodRes> {
  const result = await apiCall<CreateNeighbourhoodRes>('/neighbourhood/create-neighbourhood', {
    method: 'POST',
    body: data,
  })
  if (!result.data) throw new Error(result.message || 'No data returned')
  return result.data
}
