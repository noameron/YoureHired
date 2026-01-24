import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { streamCompanyResearch } from '../api'
import type { StreamEvent } from '@/types/api'

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
async function collectEvents(sessionId: string): Promise<StreamEvent[]> {
  const events: StreamEvent[] = []
  for await (const event of streamCompanyResearch(sessionId)) {
    events.push(event)
  }
  return events
}

describe('streamCompanyResearch', () => {
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
      expect(global.fetch).toHaveBeenCalledWith('/api/company-research/my-session-123/stream')
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
      const generator = streamCompanyResearch('test-session-id')

      // THEN
      await expect(generator.next()).rejects.toThrow('Stream failed: 404')
    })
  })

  describe('SSE event parsing', () => {
    it.each([
      {
        eventType: 'status',
        sseData: 'data: {"type":"status","message":"Planning research strategy..."}\n\n',
        expectedEvent: { type: 'status', message: 'Planning research strategy...' }
      },
      {
        eventType: 'error',
        sseData: 'data: {"type":"error","message":"Research timed out. Please try again."}\n\n',
        expectedEvent: { type: 'error', message: 'Research timed out. Please try again.' }
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

    it('yields complete events with full company data', async () => {
      // GIVEN
      const completeEventData = {
        type: 'complete',
        data: {
          name: 'Test Corp',
          description: 'A test company',
          industry: null,
          size: null,
          tech_stack: null,
          engineering_culture: null,
          recent_news: [],
          interview_tips: null,
          sources: []
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
        expect(events[0].data.name).toBe('Test Corp')
        expect(events[0].data.description).toBe('A test company')
      }
    })
  })

  describe('multiple events handling', () => {
    it('yields all events in order from stream', async () => {
      // GIVEN
      const sseData = [
        'data: {"type":"status","message":"Planning..."}\n\n',
        'data: {"type":"status","message":"Searching..."}\n\n',
        'data: {"type":"complete","data":{"name":"Test Corp","description":"A test company","industry":null,"size":null,"tech_stack":null,"engineering_culture":null,"recent_news":[],"interview_tips":null,"sources":[]}}\n\n'
      ]
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream(sseData)
      })

      // WHEN
      const events = await collectEvents('test-session-id')

      // THEN
      expect(events).toHaveLength(3)
      expect(events.map((e) => e.type)).toEqual(['status', 'status', 'complete'])
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
