/** Domain types shared across the Operator IQ frontend. */

export interface Operator {
  id: number
  matricule: string
  full_name: string
  team: string
  shift: string
  status: 'present' | 'absent' | 'conge'
  created_at: string
}

export interface Operation {
  id: number
  code: string
  name: string
  line: string
  criticality: 1 | 2 | 3 | 4 | 5
  nominal_cycle_time_s?: number
}

export interface ReplacementCandidate {
  operator_id: number
  matricule: string
  full_name: string
  score: number
  mastery_score: number
  recency_factor: number
  quality_penalty: number
  adjacency_bonus: number
  days_since_practice: number
  reason: string
}

export interface ReplacementResponse {
  operation_id: number
  operation_name: string
  shift: string
  candidates: ReplacementCandidate[]
  computation_time_ms: number
}

export interface SkillSnapshot {
  id: number
  operator_id: number
  operation_id: number
  mastery_score: number
  last_practice: string
  decay_rate: number
  total_hours: number
}

export interface OperationFragility {
  operation_id: number
  operation_name: string
  line: string
  criticality: number
  qualified_operators_count: number
  risk_level: 'CRITIQUE' | 'ÉLEVÉ' | 'MOYEN' | 'OK'
  operators_above_threshold: Array<{ operator_id: number; name: string; score: number }>
}

export interface LearningPath {
  operator_id: number
  operator_name: string
  target_operation_id: number
  target_operation_name: string
  estimated_weeks_to_qualify: number
  current_adjacent_score: number
  recommended_priority: string
}

export interface InsightsResponse {
  fragile_operations: OperationFragility[]
  learning_paths: LearningPath[]
  total_operators: number
  polyvalence_index: number
}
