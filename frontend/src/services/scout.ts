import type {
  DeveloperProfile,
  DeveloperProfileResponse,
  SearchFilters,
  SearchRunResponse,
  ScoutSearchResult,
  ScoutStreamEvent,
} from '@/types/scout'

const API_BASE = '/api'

export async function saveProfile(profile: DeveloperProfile): Promise<{ id: string }> {
  const response = await fetch(`${API_BASE}/scout/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  if (!response.ok) throw new Error(`Failed to save profile: ${response.status}`)
  return response.json()
}

export async function getProfile(): Promise<DeveloperProfileResponse | null> {
  const response = await fetch(`${API_BASE}/scout/profile`)
  if (response.status === 404) return null
  if (!response.ok) throw new Error(`Failed to fetch profile: ${response.status}`)
  return response.json()
}

export async function startSearch(filters: SearchFilters): Promise<SearchRunResponse> {
  const response = await fetch(`${API_BASE}/scout/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filters),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || `Failed to start search: ${response.status}`)
  }
  return response.json()
}

export async function* streamSearchProgress(
  runId: string,
  signal?: AbortSignal,
): AsyncGenerator<ScoutStreamEvent> {
  const url = `${API_BASE}/scout/search/${runId}/stream`
  const response = signal ? await fetch(url, { signal }) : await fetch(url)

  if (!response.ok) throw new Error(`Stream failed: ${response.status}`)
  if (!response.body) throw new Error('Response body is null')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const parsed = JSON.parse(line.slice(6))
        if (!parsed.type) throw new Error('SSE event missing "type" field')
        yield parsed as ScoutStreamEvent
      }
    }
  }
}

export async function getSearchResults(runId: string): Promise<ScoutSearchResult> {
  const response = await fetch(`${API_BASE}/scout/search/${runId}/results`)
  if (!response.ok) throw new Error(`Failed to fetch results: ${response.status}`)
  return response.json()
}

export async function cancelSearch(runId: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/scout/search/${runId}/cancel`, { method: 'POST' })
  } catch {
    // fire-and-forget: silently ignore errors
  }
}
