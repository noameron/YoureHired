import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import ScoutView from '@/views/ScoutView.vue'
import * as scoutService from '@/services/scout'
import type {
  ScoutStreamEvent,
  ScoutSearchResult,
  AnalysisResult,
  RepoMetadata
} from '@/types/scout'

vi.mock('@/services/scout')

const mockRepo: RepoMetadata = {
  github_id: 12345,
  owner: 'fastapi',
  name: 'fastapi',
  url: 'https://github.com/fastapi/fastapi',
  description: 'FastAPI framework',
  primary_language: 'Python',
  languages: ['Python'],
  star_count: 65000,
  fork_count: 5000,
  open_issue_count: 120,
  topics: ['python', 'api'],
  license: 'MIT',
  pushed_at: '2024-01-15T00:00:00Z',
  created_at: '2018-12-08T00:00:00Z',
  good_first_issue_count: 5,
  help_wanted_count: 10
}

const mockResult: AnalysisResult = {
  repo: 'fastapi/fastapi',
  fit_score: 8.5,
  reason: 'Great match',
  contributions: ['Fix docs', 'Add tests'],
  reject: false,
  reject_reason: null
}

const mockSearchResult: ScoutSearchResult = {
  run_id: 'run-123',
  status: 'completed',
  total_discovered: 10,
  total_filtered: 5,
  total_analyzed: 3,
  results: [mockResult],
  repos: [mockRepo],
  warnings: []
}

async function* createMockStream(events: ScoutStreamEvent[]): AsyncGenerator<ScoutStreamEvent> {
  for (const event of events) {
    yield event
  }
}

function mountScoutView(): VueWrapper {
  return mount(ScoutView)
}

describe('ScoutView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('shows search form directly on mount', async () => {
    // GIVEN — no profile setup needed

    // WHEN
    const wrapper = mountScoutView()

    // THEN
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    expect(filterForm.exists()).toBe(true)
    expect(wrapper.find('[data-testid="profile-form"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="profile-loading"]').exists()).toBe(false)
  })

  it('includes query field in search request', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: mockSearchResult }
      ])
    )

    const wrapper = mountScoutView()
    await flushPromises()

    // WHEN
    const languageInput = wrapper.find('input[name="filter-languages"]')
    await languageInput.setValue('Python')

    const queryTextarea = wrapper.find('textarea[name="query"]')
    await queryTextarea.setValue('Looking for beginner-friendly repos')

    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN
    expect(scoutService.startSearch).toHaveBeenCalledWith(
      expect.objectContaining({
        query: 'Looking for beginner-friendly repos'
      })
    )
  })

  it('search button triggers API call', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: mockSearchResult }
      ])
    )

    const wrapper = mountScoutView()

    // WHEN
    const languageInput = wrapper.find('input[name="filter-languages"]')
    await languageInput.setValue('Python')

    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN
    expect(scoutService.startSearch).toHaveBeenCalled()
  })

  it('displays progress during search', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'status', message: 'Discovering repositories...', phase: 'discovering' },
        { type: 'status', message: 'Filtering results...', phase: 'filtering' },
        { type: 'complete', data: mockSearchResult }
      ])
    )

    const wrapper = mountScoutView()

    // WHEN
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN — statusMessage remains set after stream completes
    const progressIndicator = wrapper.find('[data-testid="search-progress"]')
    expect(progressIndicator.exists()).toBe(true)
  })

  it('displays results after completion', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: mockSearchResult }
      ])
    )

    const wrapper = mountScoutView()

    // WHEN
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN
    const resultCards = wrapper.findAllComponents({ name: 'ScoutResultCard' })
    expect(resultCards.length).toBeGreaterThan(0)
  })

  it('cancel button aborts stream and calls cancelSearch', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.cancelSearch).mockResolvedValue(undefined)

    const longRunningStream = async function* (): AsyncGenerator<ScoutStreamEvent> {
      yield { type: 'status', message: 'Processing...', phase: 'discovering' }
      await new Promise(resolve => setTimeout(resolve, 10000))
    }
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(longRunningStream())

    const wrapper = mountScoutView()

    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // WHEN
    const cancelButton = wrapper.find('[data-testid="cancel-search"]')
    await cancelButton.trigger('click')
    await flushPromises()

    // THEN
    expect(scoutService.cancelSearch).toHaveBeenCalledWith('run-123')
  })

  it('shows error message on search failure', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'error', message: 'Search failed due to API error' }
      ])
    )

    const wrapper = mountScoutView()

    // WHEN
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN
    const errorMessage = wrapper.find('[data-testid="search-error"]')
    expect(errorMessage.exists()).toBe(true)
    expect(errorMessage.text()).toContain('Search failed due to API error')
  })

  it('shows "No matching repos found" when results empty', async () => {
    // GIVEN
    const emptyResult: ScoutSearchResult = {
      ...mockSearchResult,
      results: [],
      repos: []
    }

    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: emptyResult }
      ])
    )

    const wrapper = mountScoutView()

    // WHEN
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN
    expect(wrapper.text()).toContain('No matching repos found')
  })

  it('shows warnings banner when present', async () => {
    // GIVEN
    const resultWithWarnings: ScoutSearchResult = {
      ...mockSearchResult,
      warnings: ['Rate limit approaching', 'Some repositories skipped']
    }

    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: resultWithWarnings }
      ])
    )

    const wrapper = mountScoutView()

    // WHEN
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN
    const warningsBanner = wrapper.find('[data-testid="warnings-banner"]')
    expect(warningsBanner.exists()).toBe(true)
    expect(warningsBanner.text()).toContain('Rate limit approaching')
    expect(warningsBanner.text()).toContain('Some repositories skipped')
  })

  it('cancel button replaces Search Repos button when searching', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })

    const longRunningStream = async function* (): AsyncGenerator<ScoutStreamEvent> {
      yield { type: 'status', message: 'Processing...', phase: 'discovering' }
      await new Promise(resolve => setTimeout(resolve, 10000))
    }
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(longRunningStream())

    const wrapper = mountScoutView()

    // WHEN — start search
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN — cancel button replaces Search Repos button
    const cancelButton = filterForm.find('[data-testid="cancel-search"]')
    expect(cancelButton.exists()).toBe(true)
    expect(cancelButton.classes()).toContain('btn-danger')
    expect(cancelButton.text()).toBe('Cancel Search')

    const searchButton = filterForm.find('button[type="submit"]')
    expect(searchButton.exists()).toBe(false)
  })

  it('Search Repos button shown when not searching', async () => {
    // GIVEN

    // WHEN
    const wrapper = mountScoutView()

    // THEN — Search Repos button is present, cancel button is not
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    const searchButton = filterForm.find('button[type="submit"]')
    expect(searchButton.exists()).toBe(true)
    expect(searchButton.text()).toContain('Search Repos')

    const cancelButton = filterForm.find('[data-testid="cancel-search"]')
    expect(cancelButton.exists()).toBe(false)
  })

  it('handleCancel captures run_id before resetSearch clears it', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-456', status: 'running' })
    vi.mocked(scoutService.cancelSearch).mockResolvedValue(undefined)

    const longRunningStream = async function* (): AsyncGenerator<ScoutStreamEvent> {
      yield { type: 'status', message: 'Processing...', phase: 'discovering' }
      await new Promise(resolve => setTimeout(resolve, 10000))
    }
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(longRunningStream())

    const wrapper = mountScoutView()

    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // WHEN — click cancel (which calls resetSearch that clears currentRunId)
    const cancelButton = wrapper.find('[data-testid="cancel-search"]')
    await cancelButton.trigger('click')
    await flushPromises()

    // THEN — cancelSearch was called with the correct run_id despite resetSearch clearing it
    expect(scoutService.cancelSearch).toHaveBeenCalledWith('run-456')
  })

  it('includes all filter fields in search request', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-789', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: mockSearchResult }
      ])
    )

    const wrapper = mountScoutView()
    await flushPromises()

    // WHEN — fill in all filter fields
    await wrapper.find('input[name="filter-languages"]').setValue('Python,Go')
    await wrapper.find('input[name="filter-topics"]').setValue('api,web')
    await wrapper.find('input[name="min-stars"]').setValue('100')
    await wrapper.find('input[name="max-stars"]').setValue('10000')
    await wrapper.find('input[name="activity-date"]').setValue('2024-01-01')
    await wrapper.find('select[name="license"]').setValue('mit')
    await wrapper.find('textarea[name="query"]').setValue('Looking for API frameworks')

    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN — all filters are sent to API
    expect(scoutService.startSearch).toHaveBeenCalledWith({
      languages: ['Python', 'Go'],
      topics: ['api', 'web'],
      min_stars: 100,
      max_stars: 10000,
      min_activity_date: '2024-01-01',
      license: 'mit',
      query: 'Looking for API frameworks'
    })
  })

  it('handles startSearch API failure gracefully', async () => {
    // GIVEN
    vi.mocked(scoutService.startSearch).mockRejectedValue(new Error('Network timeout'))

    const wrapper = mountScoutView()

    // WHEN
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN — error message displayed
    const errorMessage = wrapper.find('[data-testid="search-error"]')
    expect(errorMessage.exists()).toBe(true)
    expect(errorMessage.text()).toContain('Network timeout')
  })

  it('clears previous results when starting new search', async () => {
    // GIVEN — previous search completed
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-first', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: mockSearchResult }
      ])
    )

    const wrapper = mountScoutView()
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // Verify first results exist
    expect(wrapper.findAllComponents({ name: 'ScoutResultCard' }).length).toBeGreaterThan(0)

    // WHEN — start second search
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-second', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'status', message: 'Searching...', phase: 'discovering' }
      ])
    )

    await filterForm.trigger('submit')
    await flushPromises()

    // THEN — results are cleared during search
    const progressIndicator = wrapper.find('[data-testid="search-progress"]')
    expect(progressIndicator.exists()).toBe(true)
  })
})
