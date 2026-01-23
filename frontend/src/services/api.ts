import type { RolesResponse, UserSelectionRequest, UserSelectionResult } from '@/types/api'

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
