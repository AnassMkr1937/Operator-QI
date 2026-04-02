import { apiClient } from './client'
import type { Operation } from '../types'

export async function getOperations(): Promise<Operation[]> {
  const { data } = await apiClient.get<Operation[]>('/operations')
  return data
}

export async function getOperation(id: number): Promise<Operation> {
  const { data } = await apiClient.get<Operation>(`/operations/${id}`)
  return data
}
