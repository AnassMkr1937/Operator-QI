import { useQuery } from '@tanstack/react-query'
import { fetchReplacements } from '../api/replacement'

export function useReplacement(operationId: number | null, shift = 'all') {
  return useQuery({
    queryKey: ['replacement', operationId, shift],
    queryFn: () => fetchReplacements(operationId!, shift),
    enabled: operationId !== null,
    staleTime: 0, // always fresh for replacement decisions
  })
}
