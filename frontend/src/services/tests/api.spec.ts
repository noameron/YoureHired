import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { streamDrillGeneration } from '../api'
import type { DrillStreamEvent } from '../types'

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
async function collectEvents(sessionId: string): Promise<DrillStreamEvent[]> {
  const events: DrillStreamEvent[] = []
  for await (const event of streamDrillGeneration(sessionId)) {
    events.push(event)
  }
  return events
}

describe('streamDrillGeneration', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  describe('fetch configuration', () => {
    it('calls fetch with the correct API endpoint URL', async () => {
      // GIVEN
      const sessionId = 'my-session-123'
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([])
      })

      // WHEN
      await collectEvents(sessionId)

      // THEN
      expect(global.fetch).toHaveBeenCalledWith('/api/generate-drill/my-session-123/stream')
    })
  })

  describe('error handling', () => {
    it('throws error with status code when response is not ok', async () => {
      // GIVEN
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404
      })

      // WHEN
      const generator = streamDrillGeneration('test-session-id')

      // THEN
      await expect(generator.next()).rejects.toThrow('Stream failed: 404')
    })
  })

  describe('SSE event parsing', () => {
    it.each([
      {
        eventType: 'status',
        sseData: 'data: {"type":"status","message":"Researching company..."}\n\n',
        expectedEvent: { type: 'status', message: 'Researching company...' }
      },
      {
        eventType: 'error',
        sseData: 'data: {"type":"error","message":"Drill generation timed out. Please try again."}\n\n',
        expectedEvent: { type: 'error', message: 'Drill generation timed out. Please try again.' }
      }
    ])('yields $eventType events correctly', async ({ sseData, expectedEvent }) => {
      // GIVEN
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([sseData])
      })

      // WHEN
      const events = await collectEvents('test-session-id')

      // THEN
      expect(events).toHaveLength(1)
      expect(events[0]).toEqual(expectedEvent)
    })

    it('yields candidate events correctly', async () => {
      // GIVEN
      const candidateEventData = {
        type: 'candidate',
        generator: 'coding',
        title: 'Build a Rate Limiter'
      }
      const sseData = `data: ${JSON.stringify(candidateEventData)}\n\n`
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([sseData])
      })

      // WHEN
      const events = await collectEvents('test-session-id')

      // THEN
      expect(events).toHaveLength(1)
      expect(events[0].type).toBe('candidate')
      if (events[0].type === 'candidate') {
        expect(events[0].generator).toBe('coding')
        expect(events[0].title).toBe('Build a Rate Limiter')
      }
    })

    it('yields complete events with full drill data', async () => {
      // GIVEN
      const completeEventData = {
        type: 'complete',
        data: {
          title: 'Build a Rate Limiter',
          type: 'coding',
          difficulty: 'medium',
          description: 'Implement a token bucket rate limiter.',
          requirements: ['Handle concurrent requests'],
          starter_code: null,
          hints: ['Consider using a sliding window'],
          expected_time_minutes: 45,
          tech_stack: ['Python', 'Redis'],
          company_context: 'Similar to systems used at the company.'
        }
      }
      const sseData = `data: ${JSON.stringify(completeEventData)}\n\n`
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([sseData])
      })

      // WHEN
      const events = await collectEvents('test-session-id')

      // THEN
      expect(events).toHaveLength(1)
      expect(events[0].type).toBe('complete')
      if (events[0].type === 'complete') {
        expect(events[0].data.title).toBe('Build a Rate Limiter')
        expect(events[0].data.type).toBe('coding')
        expect(events[0].data.difficulty).toBe('medium')
      }
    })
  })

  describe('multiple events handling', () => {
    it('yields all events in order from stream', async () => {
      // GIVEN
      const sseData = [
        'data: {"type":"status","message":"Researching company..."}\n\n',
        'data: {"type":"status","message":"Generating drill candidates..."}\n\n',
        'data: {"type":"candidate","generator":"coding","title":"Build a Rate Limiter"}\n\n',
        'data: {"type":"complete","data":{"title":"Build a Rate Limiter","type":"coding","difficulty":"medium","description":"Implement a rate limiter.","requirements":[],"starter_code":null,"hints":[],"expected_time_minutes":45,"tech_stack":[],"company_context":null}}\n\n'
      ]
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream(sseData)
      })

      // WHEN
      const events = await collectEvents('test-session-id')

      // THEN
      expect(events).toHaveLength(4)
      expect(events.map((e) => e.type)).toEqual(['status', 'status', 'candidate', 'complete'])
    })
  })

  describe('chunked data handling', () => {
    it('correctly reassembles events split across chunk boundaries', async () => {
      // GIVEN
      const sseData = [
        'data: {"type":"status","message":"First"}\n\ndata: {"type":"sta',
        'tus","message":"Second"}\n\n'
      ]
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream(sseData)
      })

      // WHEN
      const events = await collectEvents('test-session-id')

      // THEN
      expect(events).toHaveLength(2)
      expect(events[0]).toEqual({ type: 'status', message: 'First' })
      expect(events[1]).toEqual({ type: 'status', message: 'Second' })
    })
  })

  describe('SSE protocol compliance', () => {
    it.each([
      { lineType: 'comment', line: ': this is a comment\n' },
      { lineType: 'event field', line: 'event: custom\n' },
      { lineType: 'id field', line: 'id: 123\n' }
    ])('ignores $lineType lines in SSE stream', async ({ line }) => {
      // GIVEN
      const sseData = [line, 'data: {"type":"status","message":"Valid"}\n\n']
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream(sseData)
      })

      // WHEN
      const events = await collectEvents('test-session-id')

      // THEN
      expect(events).toHaveLength(1)
      expect(events[0]).toEqual({ type: 'status', message: 'Valid' })
    })
  })
})
