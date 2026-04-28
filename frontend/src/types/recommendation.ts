/** TypeScript types mirroring backend Pydantic schemas (app/schemas/recommendation.py). */

export type Shift = "morning" | "afternoon" | "night";

export interface RequiredSkill {
  skill_id: string;
  min_proficiency: number;
  mandatory: boolean;
}

export interface OperationContext {
  operation_id: string;
  name: string;
  required_skills: RequiredSkill[];
  assignment_date: string; // ISO 8601 date
  shift: Shift;
  category?: string | null;
}

export interface OperatorSkill {
  skill_id: string;
  proficiency: number;
  certified: boolean;
  last_used_date?: string | null;
}

export interface PastAssignment {
  operation_id: string;
  assignment_date: string;
  shift: Shift;
  category?: string | null;
}

export interface CandidateOperator {
  operator_id: string;
  name: string;
  is_active: boolean;
  skills: OperatorSkill[];
  assignments: PastAssignment[];
}

export interface RecommendationRequest {
  operation: OperationContext;
  candidates: CandidateOperator[];
  top_n: number;
}

export interface ScoreBreakdown {
  skills_score: number;
  availability_score: number;
  history_score: number;
  experience_score: number;
  raw_skills: number;
  raw_availability: number;
  raw_history: number;
  raw_experience: number;
}

export interface CandidateRecommendation {
  operator_id: string;
  name: string;
  rank: number;
  total_score: number;
  breakdown: ScoreBreakdown;
  unmet_requirements: string[];
  explanation: string;
}

export interface RecommendationResponse {
  recommendations: CandidateRecommendation[];
  total_eligible: number;
  total_candidates: number;
  operation_id: string;
  filtered_out: string[];
}
