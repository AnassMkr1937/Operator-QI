import { useQuery } from '@tanstack/react-query'
import { getOperations } from '../api/operations'

export function useOperations() {
  return useQuery({
    queryKey: ['operations'],
    queryFn: getOperations,
    staleTime: 300_000, // operations list rarely changes
  })
}
