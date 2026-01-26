import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import PracticeView from '../PracticeView.vue'
import { useUserSelectionStore } from '@/stores/userSelection'
import * as api from '@/services/api'
import type { Drill, DrillStreamEvent, DrillStreamCandidateEvent } from '@/services/types'

// Mock the API module
vi.mock('@/services/api')

// Mock vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

// Test data
const mockDrill: Drill = {
  title: 'Build a Rate Limiter',
  type: 'coding',
  difficulty: 'medium',
  description: 'Implement a token bucket rate limiter.',
  requirements: ['Handle concurrent requests', 'Support configurable limits'],
  starter_code: 'class RateLimiter:\n    pass',
  hints: ['Consider using a sliding window', 'Think about thread safety'],
  expected_time_minutes: 45,
  tech_stack: ['Python', 'Redis'],
  company_context: 'Similar to rate limiting systems used at the company.'
}

// Helper to create an async generator from events
async function* createMockStream(events: DrillStreamEvent[]): AsyncGenerator<DrillStreamEvent> {
  for (const event of events) {
    yield event
  }
}

// Helper to setup store with valid session
function setupStoreWithSession(sessionId = 'test-session-123') {
  const store = useUserSelectionStore()
  store.setSelection({
    companyName: 'Test Corp',
    role: 'Backend Developer',
    sessionId
  })
  return store
}

// Helper to mount component with store setup and API mock
async function mountWithStream(
  events: DrillStreamEvent[] | AsyncGenerator<DrillStreamEvent>
): Promise<VueWrapper> {
  setupStoreWithSession()

  if (Array.isArray(events)) {
    vi.mocked(api.streamDrillGeneration).mockReturnValue(createMockStream(events))
  } else {
    vi.mocked(api.streamDrillGeneration).mockReturnValue(events)
  }

  const wrapper = mount(PracticeView)
  await flushPromises()
  return wrapper
}

// Helper to find section by heading text
function findSection(wrapper: VueWrapper, heading: string) {
  return wrapper.findAll('.section').find((s) => s.find('h3').text() === heading)
}

describe('PracticeView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('session validation', () => {
    it('redirects to home if no sessionId', async () => {
      // Don't set sessionId - should be null/undefined
      mount(PracticeView)
      await flushPromises()

      expect(mockPush).toHaveBeenCalledWith('/')
    })

    it('does not redirect if sessionId exists', async () => {
      await mountWithStream([{ type: 'status', message: 'Starting...' }])

      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  describe('loading state', () => {
    it('shows initial connecting status', async () => {
      setupStoreWithSession()

      // Create a stream that never resolves
      const neverEndingStream = async function* (): AsyncGenerator<DrillStreamEvent> {
        await new Promise<void>(() => {
          // Never resolve
        })
      }

      vi.mocked(api.streamDrillGeneration).mockReturnValue(neverEndingStream())
      const wrapper = mount(PracticeView)

      expect(wrapper.find('.loading-state').exists()).toBe(true)
      expect(wrapper.find('.spinner').exists()).toBe(true)
    })

    it('shows company and role context while loading', async () => {
      const wrapper = await mountWithStream([{ type: 'status', message: 'Planning...' }])

      expect(wrapper.find('.context').text()).toContain('Test Corp')
      expect(wrapper.find('.context').text()).toContain('Backend Developer')
    })

    it('updates status message as events arrive', async () => {
      const events: DrillStreamEvent[] = [
        { type: 'status', message: 'Researching company...' },
        { type: 'status', message: 'Generating drill candidates...' },
        { type: 'status', message: 'Evaluating candidates...' }
      ]

      const wrapper = await mountWithStream(events)

      // After all events, should show the last status
      expect(wrapper.find('.status').text()).toBe('Evaluating candidates...')
    })

    it('shows candidates as they are generated', async () => {
      const events: DrillStreamEvent[] = [
        { type: 'status', message: 'Generating...' },
        { type: 'candidate', generator: 'coding', title: 'Build a Rate Limiter' },
        { type: 'candidate', generator: 'debugging', title: 'Fix Memory Leak' }
      ]

      const wrapper = await mountWithStream(events)

      const candidates = wrapper.findAll('.candidate-item')
      expect(candidates).toHaveLength(2)
      expect(candidates[0].text()).toContain('Coding')
      expect(candidates[0].text()).toContain('Build a Rate Limiter')
      expect(candidates[1].text()).toContain('Debugging')
      expect(candidates[1].text()).toContain('Fix Memory Leak')
    })
  })

  describe('complete state', () => {
    it('shows drill when complete event received', async () => {
      const events: DrillStreamEvent[] = [
        { type: 'status', message: 'Generating...' },
        { type: 'complete', data: mockDrill }
      ]

      const wrapper = await mountWithStream(events)

      expect(wrapper.find('.drill-card').exists()).toBe(true)
      expect(wrapper.find('.loading-state').exists()).toBe(false)
    })

    it('displays drill title', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockDrill }])

      expect(wrapper.find('.drill-card h1').text()).toBe('Build a Rate Limiter')
    })

    it('displays drill metadata', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockDrill }])

      expect(wrapper.find('.meta').text()).toContain('Coding')
      expect(wrapper.find('.meta').text()).toContain('medium')
      expect(wrapper.find('.meta').text()).toContain('45 min')
    })

    it('displays drill description', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockDrill }])

      expect(wrapper.find('.description').text()).toBe('Implement a token bucket rate limiter.')
    })

    it('displays company context when available', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockDrill }])

      const contextSection = findSection(wrapper, 'Company Context')
      expect(contextSection).toBeDefined()
      expect(contextSection!.text()).toContain('Similar to rate limiting systems')
    })

    it('displays requirements', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockDrill }])

      const reqSection = findSection(wrapper, 'Requirements')
      expect(reqSection).toBeDefined()
      expect(reqSection!.text()).toContain('Handle concurrent requests')
      expect(reqSection!.text()).toContain('Support configurable limits')
    })

    it('displays tech stack when available', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockDrill }])

      const techSection = findSection(wrapper, 'Tech Stack')
      expect(techSection).toBeDefined()
      expect(techSection!.text()).toContain('Python')
      expect(techSection!.text()).toContain('Redis')
    })

    it('displays starter code when available', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockDrill }])

      const codeSection = findSection(wrapper, 'Starter Code')
      expect(codeSection).toBeDefined()
      expect(codeSection!.find('code').text()).toContain('class RateLimiter')
    })

    it('displays hints in collapsible section', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockDrill }])

      const hintsSection = wrapper.find('.hints-section')
      expect(hintsSection.exists()).toBe(true)
      expect(hintsSection.find('summary').text()).toContain('Hints (2)')
      expect(hintsSection.text()).toContain('Consider using a sliding window')
    })

    it('hides company context section when null', async () => {
      const drillWithoutContext: Drill = {
        ...mockDrill,
        company_context: null
      }

      const wrapper = await mountWithStream([{ type: 'complete', data: drillWithoutContext }])

      const contextSection = findSection(wrapper, 'Company Context')
      expect(contextSection).toBeUndefined()
    })

    it('hides tech stack section when empty', async () => {
      const drillWithoutTech: Drill = {
        ...mockDrill,
        tech_stack: []
      }

      const wrapper = await mountWithStream([{ type: 'complete', data: drillWithoutTech }])

      const techSection = findSection(wrapper, 'Tech Stack')
      expect(techSection).toBeUndefined()
    })
  })

  describe('error state', () => {
    it('shows error message when error event received', async () => {
      const events: DrillStreamEvent[] = [
        { type: 'status', message: 'Generating...' },
        { type: 'error', message: 'Drill generation timed out. Please try again.' }
      ]

      const wrapper = await mountWithStream(events)

      expect(wrapper.find('.error-state').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toBe(
        'Drill generation timed out. Please try again.'
      )
    })

    it('shows retry button on error', async () => {
      const wrapper = await mountWithStream([{ type: 'error', message: 'Failed' }])

      expect(wrapper.find('.retry-button').exists()).toBe(true)
      expect(wrapper.find('.retry-button').text()).toBe('Try Again')
    })

    it('shows error when stream throws', async () => {
      setupStoreWithSession()

      vi.mocked(api.streamDrillGeneration).mockImplementation(async function* () {
        throw new Error('Network error')
      })

      const wrapper = mount(PracticeView)
      await flushPromises()

      expect(wrapper.find('.error-state').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toBe('Network error')
    })

    it('shows generic error for non-Error throws', async () => {
      setupStoreWithSession()

      vi.mocked(api.streamDrillGeneration).mockImplementation(async function* () {
        throw 'Unknown error'
      })

      const wrapper = mount(PracticeView)
      await flushPromises()

      expect(wrapper.find('.error-message').text()).toBe('Connection failed')
    })
  })

  describe('retry functionality', () => {
    it('calls streamDrillGeneration again when retry clicked', async () => {
      setupStoreWithSession()

      // First call returns error
      vi.mocked(api.streamDrillGeneration).mockReturnValueOnce(
        createMockStream([{ type: 'error', message: 'Failed' }])
      )

      const wrapper = mount(PracticeView)
      await flushPromises()

      expect(api.streamDrillGeneration).toHaveBeenCalledTimes(1)

      // Second call returns success
      vi.mocked(api.streamDrillGeneration).mockReturnValueOnce(
        createMockStream([{ type: 'complete', data: mockDrill }])
      )

      await wrapper.find('.retry-button').trigger('click')
      await flushPromises()

      expect(api.streamDrillGeneration).toHaveBeenCalledTimes(2)
      expect(wrapper.find('.drill-card').exists()).toBe(true)
    })

    it('clears error state when retrying', async () => {
      setupStoreWithSession()

      // First call returns error, second returns success after delay
      vi.mocked(api.streamDrillGeneration)
        .mockReturnValueOnce(createMockStream([{ type: 'error', message: 'Failed' }]))
        .mockReturnValueOnce(createMockStream([{ type: 'status', message: 'Retrying...' }]))

      const wrapper = mount(PracticeView)
      await flushPromises()

      expect(wrapper.find('.error-state').exists()).toBe(true)

      await wrapper.find('.retry-button').trigger('click')
      await flushPromises()

      expect(wrapper.find('.error-state').exists()).toBe(false)
      expect(wrapper.find('.loading-state').exists()).toBe(true)
    })

    it('clears candidates when retrying', async () => {
      setupStoreWithSession()

      // First call returns candidates then error
      vi.mocked(api.streamDrillGeneration).mockReturnValueOnce(
        createMockStream([
          { type: 'candidate', generator: 'coding', title: 'Old Candidate' },
          { type: 'error', message: 'Failed' }
        ])
      )

      const wrapper = mount(PracticeView)
      await flushPromises()

      // Error state is shown (candidates are in loading-state which is hidden on error)
      expect(wrapper.find('.error-state').exists()).toBe(true)

      // Second call returns new candidate - should not show old ones
      vi.mocked(api.streamDrillGeneration).mockReturnValueOnce(
        createMockStream([
          { type: 'status', message: 'Retrying...' },
          { type: 'candidate', generator: 'debugging', title: 'New Candidate' }
        ])
      )

      await wrapper.find('.retry-button').trigger('click')
      await flushPromises()

      // Should only show the new candidate, not the old one
      const candidates = wrapper.findAll('.candidate-item')
      expect(candidates).toHaveLength(1)
      expect(candidates[0].text()).toContain('New Candidate')
      expect(candidates[0].text()).not.toContain('Old Candidate')
    })
  })

  describe('API integration', () => {
    it('calls streamDrillGeneration with sessionId on mount', async () => {
      setupStoreWithSession('test-session-456')

      vi.mocked(api.streamDrillGeneration).mockReturnValue(
        createMockStream([{ type: 'status', message: 'Starting...' }])
      )

      mount(PracticeView)
      await flushPromises()

      expect(api.streamDrillGeneration).toHaveBeenCalledWith('test-session-456')
    })
  })
})
