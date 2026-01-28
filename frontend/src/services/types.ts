export type DrillType = 'coding' | 'debugging' | 'system_design'
export type DifficultyLevel = 'easy' | 'medium' | 'hard'

export type Drill = {
  title: string
  type: DrillType
  difficulty: DifficultyLevel
  description: string
  requirements: string[]
  starter_code: string | null
  hints: string[]
  expected_time_minutes: number
  tech_stack: string[]
  company_context: string | null
}

export type DrillStreamStatusEvent = {
  type: 'status'
  message: string
}

export type DrillStreamCandidateEvent = {
  type: 'candidate'
  generator: DrillType
  title: string
}

export type DrillStreamCompleteEvent = {
  type: 'complete'
  data: Drill
}

export type DrillStreamErrorEvent = {
  type: 'error'
  message: string
}

export type DrillStreamEvent =
  | DrillStreamStatusEvent
  | DrillStreamCandidateEvent
  | DrillStreamCompleteEvent
  | DrillStreamErrorEvent

// Solution Evaluation Types
export type StrengthItem = {
  title: string
  description: string
}

export type ImprovementItem = {
  title: string
  description: string
  suggestion: string
}

export type SolutionFeedback = {
  score: number
  strengths: StrengthItem[]
  improvements: ImprovementItem[]
  summary_for_next_drill: string
}

export type EvaluationData = {
  session_id: string
  feedback: SolutionFeedback
  feedback_file_path: string
}

export type EvaluationResponse = {
  success: true
  data: EvaluationData
}

export type EvaluationErrorDetail = {
  code: string
  message: string
}

export type EvaluationErrorResponse = {
  success: false
  error: EvaluationErrorDetail
}

export type EvaluationResult = EvaluationResponse | EvaluationErrorResponse
