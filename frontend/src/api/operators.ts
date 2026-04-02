import { apiClient } from './client'
import type { Operator } from '../types'

interface OperatorFilters {
  team?: string
  shift?: string
  status?: string
}

export async function getOperators(filters?: OperatorFilters): Promise<Operator[]> {
  const { data } = await apiClient.get<Operator[]>('/operators', { params: filters })
  return data
}

export async function getOperator(id: number): Promise<Operator> {
  const { data } = await apiClient.get<Operator>(`/operators/${id}`)
  return data
}

export async function createOperator(payload: Omit<Operator, 'id' | 'created_at'>): Promise<Operator> {
  const { data } = await apiClient.post<Operator>('/operators', payload)
  return data
}

export async function updateOperator(id: number, payload: Partial<Operator>): Promise<Operator> {
  const { data } = await apiClient.patch<Operator>(`/operators/${id}`, payload)
  return data
}

export async function deleteOperator(id: number): Promise<void> {
  await apiClient.delete(`/operators/${id}`)
}
