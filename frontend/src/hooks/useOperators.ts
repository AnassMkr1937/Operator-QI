/**
 * React Query hook for operators data.
 * Provides operators list with filtering, loading state, and error handling.
 */
import { useQuery } from '@tanstack/react-query'
import { getOperators } from '../api/operators'

interface OperatorFilters {
  team?: string
  shift?: string
  status?: string
}

export function useOperators(filters?: OperatorFilters) {
  return useQuery({
    queryKey: ['operators', filters],
    queryFn: () => getOperators(filters),
    staleTime: 60_000,
  })
}
