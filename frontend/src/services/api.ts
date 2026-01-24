import type {
  RolesResponse,
  UserSelectionRequest,
  UserSelectionResult,
  StreamEvent
} from '@/types/api'

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
 * Stream company research progress via Server-Sent Events.
 * Yields events as they arrive from the backend.
 */
export async function* streamCompanyResearch(
  sessionId: string
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${API_BASE}/company-research/${sessionId}/stream`)

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
        yield JSON.parse(line.slice(6)) as StreamEvent
      }
    }
  }
}
