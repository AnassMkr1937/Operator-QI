import { apiClient } from './client'
import type { ReplacementResponse } from '../types'

export async function fetchReplacements(
  operationId: number,
  shift = 'all'
): Promise<ReplacementResponse> {
  const { data } = await apiClient.get<ReplacementResponse>('/replacement', {
    params: { operation_id: operationId, shift },
  })
  return data
}
