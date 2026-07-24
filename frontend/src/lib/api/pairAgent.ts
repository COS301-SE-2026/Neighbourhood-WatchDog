import { LinkPropertyTokenRes } from "@/lib/validators/pairAgent"
import { apiCall } from './client'

export async function getPairingToken(propertyId: string): Promise<LinkPropertyTokenRes> {
  return apiCall<LinkPropertyTokenRes>(`/pairing-token/${propertyId}`, {
    method: 'GET',
  })
}