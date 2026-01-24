import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import PracticeView from '../PracticeView.vue'
import { useUserSelectionStore } from '@/stores/userSelection'
import * as api from '@/services/api'
import type { CompanySummary, StreamEvent } from '@/types/api'

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
const mockCompanySummary: CompanySummary = {
  name: 'Test Corp',
  industry: 'Technology',
  description: 'A leading technology company.',
  size: '1000-5000',
  tech_stack: {
    languages: ['TypeScript', 'Python'],
    frameworks: ['Vue', 'FastAPI'],
    tools: ['Docker', 'Kubernetes']
  },
  engineering_culture: 'Collaborative and innovative.',
  recent_news: ['Launched new product', 'Raised Series B'],
  interview_tips: 'Focus on system design and algorithms.',
  sources: ['https://example.com']
}

// Helper to create an async generator from events
async function* createMockStream(events: StreamEvent[]): AsyncGenerator<StreamEvent> {
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
  events: StreamEvent[] | AsyncGenerator<StreamEvent>
): Promise<VueWrapper> {
  setupStoreWithSession()

  if (Array.isArray(events)) {
    vi.mocked(api.streamCompanyResearch).mockReturnValue(createMockStream(events))
  } else {
    vi.mocked(api.streamCompanyResearch).mockReturnValue(events)
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
      const neverEndingStream = async function* (): AsyncGenerator<StreamEvent> {
        await new Promise<void>(() => {
          // Never resolve
        })
      }

      vi.mocked(api.streamCompanyResearch).mockReturnValue(neverEndingStream())
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
      const events: StreamEvent[] = [
        { type: 'status', message: 'Planning research strategy...' },
        { type: 'status', message: 'Searching (1/3): Company overview' },
        { type: 'status', message: 'Analyzing findings...' }
      ]

      const wrapper = await mountWithStream(events)

      // After all events, should show the last status
      expect(wrapper.find('.status').text()).toBe('Analyzing findings...')
    })
  })

  describe('complete state', () => {
    it('shows summary when complete event received', async () => {
      const events: StreamEvent[] = [
        { type: 'status', message: 'Planning...' },
        { type: 'complete', data: mockCompanySummary }
      ]

      const wrapper = await mountWithStream(events)

      expect(wrapper.find('.summary-state').exists()).toBe(true)
      expect(wrapper.find('.loading-state').exists()).toBe(false)
    })

    it('displays company name in summary', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockCompanySummary }])

      expect(wrapper.find('.summary-state h1').text()).toBe('Test Corp')
    })

    it('displays company description', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockCompanySummary }])

      expect(wrapper.find('.description').text()).toBe('A leading technology company.')
    })

    it('displays tech stack when available', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockCompanySummary }])

      const techStackSection = findSection(wrapper, 'Tech Stack')
      expect(techStackSection).toBeDefined()
      expect(techStackSection!.text()).toContain('TypeScript')
      expect(techStackSection!.text()).toContain('Vue')
      expect(techStackSection!.text()).toContain('Docker')
    })

    it('displays engineering culture when available', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockCompanySummary }])

      const cultureSection = findSection(wrapper, 'Engineering Culture')
      expect(cultureSection).toBeDefined()
      expect(cultureSection!.text()).toContain('Collaborative and innovative.')
    })

    it('displays interview tips when available', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockCompanySummary }])

      const tipsSection = findSection(wrapper, 'Interview Tips')
      expect(tipsSection).toBeDefined()
      expect(tipsSection!.text()).toContain('Focus on system design and algorithms.')
    })

    it('displays recent news when available', async () => {
      const wrapper = await mountWithStream([{ type: 'complete', data: mockCompanySummary }])

      const newsSection = findSection(wrapper, 'Recent News')
      expect(newsSection).toBeDefined()
      expect(newsSection!.text()).toContain('Launched new product')
      expect(newsSection!.text()).toContain('Raised Series B')
    })

    it('hides tech stack section when null', async () => {
      const summaryWithoutTech: CompanySummary = {
        ...mockCompanySummary,
        tech_stack: null
      }

      const wrapper = await mountWithStream([{ type: 'complete', data: summaryWithoutTech }])

      const techStackSection = findSection(wrapper, 'Tech Stack')
      expect(techStackSection).toBeUndefined()
    })
  })

  describe('error state', () => {
    it('shows error message when error event received', async () => {
      const events: StreamEvent[] = [
        { type: 'status', message: 'Planning...' },
        { type: 'error', message: 'Research timed out. Please try again.' }
      ]

      const wrapper = await mountWithStream(events)

      expect(wrapper.find('.error-state').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toBe('Research timed out. Please try again.')
    })

    it('shows retry button on error', async () => {
      const wrapper = await mountWithStream([{ type: 'error', message: 'Failed' }])

      expect(wrapper.find('.retry-button').exists()).toBe(true)
      expect(wrapper.find('.retry-button').text()).toBe('Try Again')
    })

    it('shows error when stream throws', async () => {
      setupStoreWithSession()

      vi.mocked(api.streamCompanyResearch).mockImplementation(async function* () {
        throw new Error('Network error')
      })

      const wrapper = mount(PracticeView)
      await flushPromises()

      expect(wrapper.find('.error-state').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toBe('Network error')
    })

    it('shows generic error for non-Error throws', async () => {
      setupStoreWithSession()

      vi.mocked(api.streamCompanyResearch).mockImplementation(async function* () {
        throw 'Unknown error'
      })

      const wrapper = mount(PracticeView)
      await flushPromises()

      expect(wrapper.find('.error-message').text()).toBe('Connection failed')
    })
  })

  describe('retry functionality', () => {
    it('calls streamCompanyResearch again when retry clicked', async () => {
      setupStoreWithSession()

      // First call returns error
      vi.mocked(api.streamCompanyResearch).mockReturnValueOnce(
        createMockStream([{ type: 'error', message: 'Failed' }])
      )

      const wrapper = mount(PracticeView)
      await flushPromises()

      expect(api.streamCompanyResearch).toHaveBeenCalledTimes(1)

      // Second call returns success
      vi.mocked(api.streamCompanyResearch).mockReturnValueOnce(
        createMockStream([{ type: 'complete', data: mockCompanySummary }])
      )

      await wrapper.find('.retry-button').trigger('click')
      await flushPromises()

      expect(api.streamCompanyResearch).toHaveBeenCalledTimes(2)
      expect(wrapper.find('.summary-state').exists()).toBe(true)
    })

    it('clears error state when retrying', async () => {
      setupStoreWithSession()

      // First call returns error, second returns success after delay
      vi.mocked(api.streamCompanyResearch)
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
  })

  describe('API integration', () => {
    it('calls streamCompanyResearch with sessionId on mount', async () => {
      setupStoreWithSession('test-session-456')

      vi.mocked(api.streamCompanyResearch).mockReturnValue(
        createMockStream([{ type: 'status', message: 'Starting...' }])
      )

      mount(PracticeView)
      await flushPromises()

      expect(api.streamCompanyResearch).toHaveBeenCalledWith('test-session-456')
    })
  })
})
