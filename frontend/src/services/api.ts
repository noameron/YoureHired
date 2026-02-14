import type {
  RolesResponse,
  UserSelectionRequest,
  UserSelectionResult
} from '@/types/api'
import type { DrillStreamEvent, EvaluationResult } from './types'

const API_BASE = '/api'

/**
 * Fetch all available roles from the API.
 * @returns Promise resolving to the roles response
 */
export async function fetchRoles(): Promise<RolesResponse> {
  const response = await fetch(`${API_BASE}/roles`)

  if (!response.ok) {
    throw new Error(`Failed to fetch roles: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

/**
 * Submit user selection to start a practice session.
 * @param data - The user selection data (company name, role, optional description)
 * @returns Promise resolving to success response or error response
 */
export async function submitUserSelection(
  data: UserSelectionRequest
): Promise<UserSelectionResult> {
  const response = await fetch(`${API_BASE}/user-selection`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })

  // Both 200 and 400 responses are valid JSON responses
  if (response.ok || response.status === 400) {
    return response.json()
  }

  // For other errors (422, 500, etc.), throw
  throw new Error(`Failed to submit user selection: ${response.status} ${response.statusText}`)
}

/**
 * Stream drill generation progress via Server-Sent Events.
 * Runs company research internally if needed, then generates drill.
 * Yields events as they arrive from the backend.
 */
export async function* streamDrillGeneration(
  sessionId: string,
  signal?: AbortSignal
): AsyncGenerator<DrillStreamEvent> {
  const url = `${API_BASE}/generate-drill/${sessionId}/stream`
  const response = signal ? await fetch(url, { signal }) : await fetch(url)

  if (!response.ok) {
    throw new Error(`Stream failed: ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || '' // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice(6)) as DrillStreamEvent
      }
    }
  }
}

/**
 * Cancel active agent generation for a session.
 * Tells the backend to stop all running agents.
 * Fire-and-forget: silently ignores all errors.
 */
export async function cancelGeneration(sessionId: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/cancel/${sessionId}`, { method: 'POST' })
  } catch {
    // fire-and-forget: silently ignore errors
  }
}

/**
 * Submit a solution for evaluation.
 * @param sessionId - The session ID
 * @param solution - The user's solution code
 * @returns Promise resolving to evaluation result
 */
export async function submitSolution(
  sessionId: string,
  solution: string
): Promise<EvaluationResult> {
  // Validate solution is not empty
  if (!solution || !solution.trim()) {
    return {
      success: false,
      error: {
        code: 'empty_solution',
        message: 'Please enter a solution before submitting.'
      }
    }
  }

  const response = await fetch(`${API_BASE}/evaluate-solution/${sessionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ solution })
  })

  // Success response
  if (response.ok) {
    return response.json()
  }

  // Error responses (400, 404, 500) - FastAPI returns {"detail": {...}}
  const errorData = await response.json()
  if (errorData.detail) {
    return {
      success: false,
      error: errorData.detail
    }
  }

  throw new Error(`Failed to submit solution: ${response.status} ${response.statusText}`)
}
