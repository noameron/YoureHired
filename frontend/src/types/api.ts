export interface Role {
  id: string
  label: string
}

export interface RolesResponse {
  roles: Role[]
}

export interface UserSelectionRequest {
  company_name: string
  role: string
  role_description?: string
}

export interface UserSelectionData {
  company_name: string
  role: string
  role_description: string | null
  session_id: string
}

export interface UserSelectionResponse {
  success: true
  data: UserSelectionData
  next_step: string
}

export interface UserSelectionErrorDetails {
  code: string
  message: string
  details: Record<string, string>
}

export interface UserSelectionError {
  success: false
  error: UserSelectionErrorDetails
}

export type UserSelectionResult = UserSelectionResponse | UserSelectionError

// Company research types
export interface TechStack {
  languages: string[]
  frameworks: string[]
  tools: string[]
}

export interface CompanySummary {
  name: string
  industry: string | null
  description: string
  size: string | null
  tech_stack: TechStack | null
  engineering_culture: string | null
  recent_news: string[]
  interview_tips: string | null
  sources: string[]
}

// Streaming event types
export interface StreamStatusEvent {
  type: 'status'
  message: string
}

export interface StreamCompleteEvent {
  type: 'complete'
  data: CompanySummary
}

export interface StreamErrorEvent {
  type: 'error'
  message: string
}

export type StreamEvent = StreamStatusEvent | StreamCompleteEvent | StreamErrorEvent
