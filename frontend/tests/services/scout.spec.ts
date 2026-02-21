import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { startSearch, streamSearchProgress, getSearchResults, cancelSearch } from '@/services/scout'
import type { ScoutStreamEvent } from '@/types/scout'

declare const global: { fetch: typeof fetch }

// Helper to create a mock ReadableStream from SSE data
function createMockSSEStream(events: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  let index = 0

  return new ReadableStream({
    pull(controller) {
      if (index < events.length) {
        controller.enqueue(encoder.encode(events[index]))
        index++
      } else {
        controller.close()
      }
    }
  })
}

// Helper to collect all events from the generator
async function collectEvents(runId: string, signal?: AbortSignal): Promise<ScoutStreamEvent[]> {
  const events: ScoutStreamEvent[] = []
  for await (const event of streamSearchProgress(runId, signal)) {
    events.push(event)
  }
  return events
}

describe('startSearch', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  it('sends POST to /api/scout/search with JSON body and returns SearchRunResponse on 200', async () => {
    // GIVEN
    const searchParams = {
      languages: ['TypeScript'],
      min_stars: 10,
      max_stars: 1000,
      topics: [],
      min_activity_date: null,
      license: null
    }
    const mockResponse = {
      run_id: 'run-abc-123',
      status: 'running'
    }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    })

    // WHEN
    const result = await startSearch(searchParams)

    // THEN
    expect(global.fetch).toHaveBeenCalledWith('/api/scout/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(searchParams)
    })
    expect(result).toEqual(mockResponse)
  })

  it('throws error with detail message on HTTP 429', async () => {
    // GIVEN
    const errorDetail = 'Rate limit exceeded: 5 searches per hour. Try again in 45 minutes.'
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({ detail: errorDetail })
    })

    // WHEN
    const searchPromise = startSearch({
      languages: ['TypeScript'],
      min_stars: 10,
      max_stars: 1000,
      topics: [],
      min_activity_date: null,
      license: null
    })

    // THEN
    await expect(searchPromise).rejects.toThrow(errorDetail)
  })

  it('throws error with detail message on non-ok response with detail', async () => {
    // GIVEN
    const errorDetail = 'Invalid language specified'
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: errorDetail })
    })

    // WHEN
    const searchPromise = startSearch({
      languages: ['InvalidLanguage'],
      min_stars: 10,
      max_stars: 1000,
      topics: [],
      min_activity_date: null,
      license: null
    })

    // THEN
    await expect(searchPromise).rejects.toThrow(errorDetail)
  })
})

describe('streamSearchProgress', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  it('yields events from SSE stream', async () => {
    // GIVEN
    const sseData = [
      'data: {"type":"phase","phase":"discover","message":"Discovering repositories..."}\n\n',
      'data: {"type":"progress","current":5,"total":10,"message":"Processing..."}\n\n',
      'data: {"type":"complete","run_id":"run-123"}\n\n'
    ]
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream(sseData)
    })

    // WHEN
    const events = await collectEvents('run-123')

    // THEN
    expect(events).toHaveLength(3)
    expect(events[0]).toEqual({ type: 'phase', phase: 'discover', message: 'Discovering repositories...' })
    expect(events[1]).toEqual({ type: 'progress', current: 5, total: 10, message: 'Processing...' })
    expect(events[2]).toEqual({ type: 'complete', run_id: 'run-123' })
  })

  it('handles stream end gracefully with empty stream', async () => {
    // GIVEN
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream([])
    })

    // WHEN
    const events = await collectEvents('run-123')

    // THEN
    expect(events).toHaveLength(0)
  })

  it('passes AbortSignal to fetch when provided', async () => {
    // GIVEN
    const runId = 'run-abc-123'
    const abortController = new AbortController()
    const signal = abortController.signal
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream([])
    })

    // WHEN
    const generator = streamSearchProgress(runId, signal)
    await generator.next()

    // THEN
    expect(global.fetch).toHaveBeenCalledWith(`/api/scout/search/${runId}/stream`, {
      signal
    })
  })

  it('throws on non-ok response', async () => {
    // GIVEN
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404
    })

    // WHEN
    const generator = streamSearchProgress('run-123')

    // THEN
    await expect(generator.next()).rejects.toThrow('Stream failed: 404')
  })

  it('throws when SSE event is missing type field', async () => {
    // GIVEN
    const sseData = [
      'data: {"message":"no type field"}\n\n'
    ]
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream(sseData)
    })

    // WHEN
    const generator = streamSearchProgress('run-123')

    // THEN
    await expect(generator.next()).rejects.toThrow('SSE event missing "type" field')
  })
})

describe('getSearchResults', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  it('sends GET to /api/scout/search/{runId}/results and returns ScoutSearchResult on 200', async () => {
    // GIVEN
    const runId = 'run-abc-123'
    const mockResults = {
      run_id: runId,
      status: 'complete',
      results: [
        {
          full_name: 'facebook/react',
          stars: 200000,
          language: 'JavaScript',
          analysis_summary: 'Great for learning React patterns'
        }
      ],
      warnings: [],
      total_discovered: 50,
      total_filtered: 10,
      total_analyzed: 5
    }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResults
    })

    // WHEN
    const result = await getSearchResults(runId)

    // THEN
    expect(global.fetch).toHaveBeenCalledWith(`/api/scout/search/${runId}/results`)
    expect(result).toEqual(mockResults)
  })

  it('throws on error response', async () => {
    // GIVEN
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal server error' })
    })

    // WHEN
    const resultPromise = getSearchResults('run-123')

    // THEN
    await expect(resultPromise).rejects.toThrow()
  })
})

describe('cancelSearch', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  it('sends POST to /api/scout/search/{runId}/cancel and resolves on success', async () => {
    // GIVEN
    const runId = 'run-abc-123'
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true })
    })

    // WHEN
    const result = cancelSearch(runId)

    // THEN
    expect(global.fetch).toHaveBeenCalledWith(`/api/scout/search/${runId}/cancel`, {
      method: 'POST'
    })
    await expect(result).resolves.toBeUndefined()
  })

  it('does not throw on fetch failure (fire-and-forget)', async () => {
    // GIVEN
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    // WHEN
    const result = cancelSearch('run-123')

    // THEN - fire-and-forget, no error thrown
    await expect(result).resolves.toBeUndefined()
  })
})
