import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import ScoutView from '@/views/ScoutView.vue'
import { useScoutStore } from '@/stores/scout'
import * as scoutService from '@/services/scout'
import type {
  DeveloperProfile,
  DeveloperProfileResponse,
  ScoutStreamEvent,
  ScoutSearchResult,
  AnalysisResult,
  RepoMetadata
} from '@/types/scout'

vi.mock('@/services/scout')

const mockProfile: DeveloperProfile = {
  languages: ['Python', 'TypeScript'],
  topics: ['web', 'api'],
  skill_level: 'intermediate',
  goals: 'Contribute to open source'
}

const mockProfileResponse: DeveloperProfileResponse = {
  id: 'profile-123',
  profile: mockProfile,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null
}

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

  it('renders profile form when no profile exists', async () => {
    // GIVEN
    vi.mocked(scoutService.getProfile).mockResolvedValue(null)

    // WHEN
    const wrapper = mountScoutView()
    await flushPromises()

    // THEN
    const profileForm = wrapper.find('[data-testid="profile-form"]')
    expect(profileForm.exists()).toBe(true)
    expect(wrapper.find('input[name="languages"]').exists()).toBe(true)
    expect(wrapper.find('input[name="topics"]').exists()).toBe(true)
    expect(wrapper.find('input[type="radio"][value="beginner"]').exists()).toBe(true)
    expect(wrapper.find('input[type="radio"][value="intermediate"]').exists()).toBe(true)
    expect(wrapper.find('input[type="radio"][value="advanced"]').exists()).toBe(true)
    expect(wrapper.find('textarea[name="goals"]').exists()).toBe(true)
    expect(wrapper.find('button').text()).toContain('Save Profile')
  })

  it('loads existing profile on mount', async () => {
    // GIVEN
    vi.mocked(scoutService.getProfile).mockResolvedValue(mockProfileResponse)

    // WHEN
    mountScoutView()
    await flushPromises()

    // THEN
    const store = useScoutStore()
    expect(store.profile).toEqual(mockProfileResponse)
  })

  it('shows filter form after profile saved', async () => {
    // GIVEN
    vi.mocked(scoutService.getProfile).mockResolvedValue(mockProfileResponse)

    // WHEN
    const wrapper = mountScoutView()
    await flushPromises()

    // THEN
    const filterForm = wrapper.find('[data-testid="filter-form"]')
    expect(filterForm.exists()).toBe(true)
  })

  it('search button triggers API call', async () => {
    // GIVEN
    vi.mocked(scoutService.getProfile).mockResolvedValue(mockProfileResponse)
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

    const filterForm = wrapper.find('[data-testid="filter-form"]')
    await filterForm.trigger('submit')
    await flushPromises()

    // THEN
    expect(scoutService.startSearch).toHaveBeenCalled()
  })

  it('displays progress during search', async () => {
    // GIVEN
    vi.mocked(scoutService.getProfile).mockResolvedValue(mockProfileResponse)
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'status', message: 'Discovering repositories...', phase: 'discovering' },
        { type: 'status', message: 'Filtering results...', phase: 'filtering' },
        { type: 'complete', data: mockSearchResult }
      ])
    )

    const wrapper = mountScoutView()
    await flushPromises()

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
    vi.mocked(scoutService.getProfile).mockResolvedValue(mockProfileResponse)
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: mockSearchResult }
      ])
    )

    const wrapper = mountScoutView()
    await flushPromises()

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
    vi.mocked(scoutService.getProfile).mockResolvedValue(mockProfileResponse)
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.cancelSearch).mockResolvedValue(undefined)

    const longRunningStream = async function* (): AsyncGenerator<ScoutStreamEvent> {
      yield { type: 'status', message: 'Processing...', phase: 'discovering' }
      await new Promise(resolve => setTimeout(resolve, 10000))
    }
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(longRunningStream())

    const wrapper = mountScoutView()
    await flushPromises()

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
    vi.mocked(scoutService.getProfile).mockResolvedValue(mockProfileResponse)
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'error', message: 'Search failed due to API error' }
      ])
    )

    const wrapper = mountScoutView()
    await flushPromises()

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

    vi.mocked(scoutService.getProfile).mockResolvedValue(mockProfileResponse)
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: emptyResult }
      ])
    )

    const wrapper = mountScoutView()
    await flushPromises()

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

    vi.mocked(scoutService.getProfile).mockResolvedValue(mockProfileResponse)
    vi.mocked(scoutService.startSearch).mockResolvedValue({ run_id: 'run-123', status: 'running' })
    vi.mocked(scoutService.streamSearchProgress).mockReturnValue(
      createMockStream([
        { type: 'complete', data: resultWithWarnings }
      ])
    )

    const wrapper = mountScoutView()
    await flushPromises()

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

  it('shows loading spinner while profile loads', async () => {
    // GIVEN — getProfile never resolves during this check
    vi.mocked(scoutService.getProfile).mockReturnValue(new Promise(() => {}))

    // WHEN
    const wrapper = mountScoutView()
    await flushPromises()

    // THEN
    expect(wrapper.find('[data-testid="profile-loading"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="profile-form"]').exists()).toBe(false)
  })

  it('shows validation errors when submitting empty profile', async () => {
    // GIVEN
    vi.mocked(scoutService.getProfile).mockResolvedValue(null)
    const wrapper = mountScoutView()
    await flushPromises()

    // WHEN — submit with empty fields
    const form = wrapper.find('[data-testid="profile-form"] form')
    await form.trigger('submit')
    await flushPromises()

    // THEN
    expect(wrapper.text()).toContain('At least one language is required')
    expect(wrapper.text()).toContain('Goals are required')
    expect(scoutService.saveProfile).not.toHaveBeenCalled()
  })

  it('clears language validation error when user types a language', async () => {
    // GIVEN
    vi.mocked(scoutService.getProfile).mockResolvedValue(null)
    const wrapper = mountScoutView()
    await flushPromises()

    const form = wrapper.find('[data-testid="profile-form"] form')
    await form.trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('At least one language is required')

    // WHEN
    await wrapper.find('input[name="languages"]').setValue('Python')
    await flushPromises()

    // THEN
    expect(wrapper.text()).not.toContain('At least one language is required')
  })

  it('clears goals validation error when user types goals', async () => {
    // GIVEN
    vi.mocked(scoutService.getProfile).mockResolvedValue(null)
    const wrapper = mountScoutView()
    await flushPromises()

    const form = wrapper.find('[data-testid="profile-form"] form')
    await form.trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('Goals are required')

    // WHEN
    await wrapper.find('textarea[name="goals"]').setValue('Learn open source')
    await flushPromises()

    // THEN
    expect(wrapper.text()).not.toContain('Goals are required')
  })

  it('shows save error when profile save fails', async () => {
    // GIVEN
    vi.mocked(scoutService.getProfile).mockResolvedValue(null)
    vi.mocked(scoutService.saveProfile).mockRejectedValue(new Error('Network error'))
    const wrapper = mountScoutView()
    await flushPromises()

    await wrapper.find('input[name="languages"]').setValue('Python')
    await wrapper.find('textarea[name="goals"]').setValue('Contribute')

    // WHEN
    const form = wrapper.find('[data-testid="profile-form"] form')
    await form.trigger('submit')
    await flushPromises()

    // THEN
    const saveError = wrapper.find('[data-testid="profile-save-error"]')
    expect(saveError.exists()).toBe(true)
    expect(saveError.text()).toContain('Network error')
  })
})
