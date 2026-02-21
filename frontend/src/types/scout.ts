export interface SearchFilters {
  languages: string[]
  min_stars: number
  max_stars: number
  topics: string[]
  min_activity_date: string | null
  license: string | null
  query: string
}

export interface RepoMetadata {
  github_id: number
  owner: string
  name: string
  url: string
  description: string | null
  primary_language: string | null
  languages: string[]
  star_count: number
  fork_count: number
  open_issue_count: number
  topics: string[]
  license: string | null
  pushed_at: string | null
  created_at: string | null
  good_first_issue_count: number
  help_wanted_count: number
}

export interface AnalysisResult {
  repo: string
  fit_score: number
  reason: string
  contributions: string[]
  reject: boolean
  reject_reason: string | null
}

export interface SearchRunResponse {
  run_id: string
  status: string
}

export interface ScoutSearchResult {
  run_id: string
  status: string
  total_discovered: number
  total_filtered: number
  total_analyzed: number
  results: AnalysisResult[]
  repos: RepoMetadata[]
  warnings: string[]
}

// SSE event types (discriminated union)
export interface ScoutStreamStatusEvent {
  type: 'status'
  message: string
  phase?: 'discovering' | 'filtering' | 'analyzing'
}

export interface ScoutStreamCompleteEvent {
  type: 'complete'
  data: ScoutSearchResult
}

export interface ScoutStreamErrorEvent {
  type: 'error'
  message: string
}

export type ScoutStreamEvent =
  | ScoutStreamStatusEvent
  | ScoutStreamCompleteEvent
  | ScoutStreamErrorEvent
