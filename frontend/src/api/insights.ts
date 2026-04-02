import { apiClient } from './client'
import type { InsightsResponse, OperationFragility, LearningPath } from '../types'

export async function getInsights(): Promise<InsightsResponse> {
  const { data } = await apiClient.get<InsightsResponse>('/insights')
  return data
}

export async function getFragilities(): Promise<OperationFragility[]> {
  const { data } = await apiClient.get<OperationFragility[]>('/insights/fragilities')
  return data
}

export async function getLearningPaths(): Promise<LearningPath[]> {
  const { data } = await apiClient.get<LearningPath[]>('/insights/learning-paths')
  return data
}
