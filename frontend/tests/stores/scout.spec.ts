import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useScoutStore } from '@/stores/scout'
import type { ScoutSearchResult } from '@/types/scout'

describe('scout store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('initial state', () => {
    it('has results initialized to empty array', () => {
      // GIVEN - a fresh store instance
      const store = useScoutStore()

      // WHEN - accessing initial state
      // (no action needed)

      // THEN - results is empty array
      expect(store.results).toEqual([])
    })

    it('has isSearching initialized to false', () => {
      // GIVEN - a fresh store instance
      const store = useScoutStore()

      // WHEN - accessing initial state
      // (no action needed)

      // THEN - isSearching is false
      expect(store.isSearching).toBe(false)
    })

    it('has error initialized to null', () => {
      // GIVEN - a fresh store instance
      const store = useScoutStore()

      // WHEN - accessing initial state
      // (no action needed)

      // THEN - error is null
      expect(store.error).toBeNull()
    })
  })

  describe('canSearch getter', () => {
    it('returns false when languages is empty', () => {
      // GIVEN - a fresh store instance
      const store = useScoutStore()

      // WHEN - accessing canSearch getter
      const result = store.canSearch

      // THEN - returns false
      expect(result).toBe(false)
    })

    it('returns true when languages has items', () => {
      // GIVEN - a store with languages set
      const store = useScoutStore()
      store.filters.languages = ['TypeScript', 'Python']

      // WHEN - accessing canSearch getter
      const result = store.canSearch

      // THEN - returns true
      expect(result).toBe(true)
    })
  })

  describe('hasResults getter', () => {
    it('returns false when results is empty array', () => {
      // GIVEN - a fresh store instance
      const store = useScoutStore()

      // WHEN - accessing hasResults getter
      const result = store.hasResults

      // THEN - returns false
      expect(result).toBe(false)
    })

    it('returns true after setSearchResult with results', () => {
      // GIVEN - a store with search results
      const store = useScoutStore()
      const mockSearchResult: ScoutSearchResult = {
        run_id: 'run-123',
        status: 'complete',
        results: [
          {
            repo: 'facebook/react',
            fit_score: 85,
            reason: 'Great for learning React patterns',
            contributions: ['Add tests', 'Fix bugs'],
            reject: false,
            reject_reason: null
          }
        ],
        repos: [
          {
            github_id: 10270250,
            owner: 'facebook',
            name: 'react',
            url: 'https://github.com/facebook/react',
            description: 'A JavaScript library for building user interfaces',
            primary_language: 'JavaScript',
            languages: ['JavaScript'],
            star_count: 200000,
            fork_count: 40000,
            open_issue_count: 500,
            topics: ['react', 'javascript'],
            license: 'MIT',
            pushed_at: '2026-02-14T00:00:00Z',
            created_at: '2013-05-24T00:00:00Z',
            good_first_issue_count: 10,
            help_wanted_count: 5
          }
        ],
        warnings: [],
        total_discovered: 50,
        total_filtered: 10,
        total_analyzed: 5
      }
      store.setSearchResult(mockSearchResult)

      // WHEN - accessing hasResults getter
      const result = store.hasResults

      // THEN - returns true
      expect(result).toBe(true)
    })
  })

  describe('setSearchResult action', () => {
    it('populates results, repos, warnings, totalDiscovered, totalFiltered, totalAnalyzed, searchStatus', () => {
      // GIVEN - a fresh store instance
      const store = useScoutStore()
      const mockSearchResult: ScoutSearchResult = {
        run_id: 'run-123',
        status: 'complete',
        results: [
          {
            repo: 'facebook/react',
            fit_score: 85,
            reason: 'Great for learning React patterns',
            contributions: ['Add tests', 'Fix bugs'],
            reject: false,
            reject_reason: null
          },
          {
            repo: 'vuejs/core',
            fit_score: 90,
            reason: 'Vue 3 core repository',
            contributions: ['Add features', 'Improve docs'],
            reject: false,
            reject_reason: null
          }
        ],
        repos: [
          {
            github_id: 10270250,
            owner: 'facebook',
            name: 'react',
            url: 'https://github.com/facebook/react',
            description: 'A JavaScript library for building user interfaces',
            primary_language: 'JavaScript',
            languages: ['JavaScript'],
            star_count: 200000,
            fork_count: 40000,
            open_issue_count: 500,
            topics: ['react', 'javascript'],
            license: 'MIT',
            pushed_at: '2026-02-14T00:00:00Z',
            created_at: '2013-05-24T00:00:00Z',
            good_first_issue_count: 10,
            help_wanted_count: 5
          },
          {
            github_id: 11730342,
            owner: 'vuejs',
            name: 'core',
            url: 'https://github.com/vuejs/core',
            description: 'Vue.js 3 core',
            primary_language: 'TypeScript',
            languages: ['TypeScript'],
            star_count: 40000,
            fork_count: 8000,
            open_issue_count: 200,
            topics: ['vue', 'typescript'],
            license: 'MIT',
            pushed_at: '2026-02-14T00:00:00Z',
            created_at: '2018-06-01T00:00:00Z',
            good_first_issue_count: 5,
            help_wanted_count: 3
          }
        ],
        warnings: ['Warning: Some repos were skipped'],
        total_discovered: 50,
        total_filtered: 10,
        total_analyzed: 5
      }

      // WHEN - setting search result
      store.setSearchResult(mockSearchResult)

      // THEN - all properties are populated correctly
      expect(store.results).toEqual(mockSearchResult.results)
      expect(store.repos).toEqual(mockSearchResult.repos)
      expect(store.warnings).toEqual(mockSearchResult.warnings)
      expect(store.totalDiscovered).toBe(50)
      expect(store.totalFiltered).toBe(10)
      expect(store.totalAnalyzed).toBe(5)
      expect(store.searchStatus).toBe('complete')
    })
  })

  describe('resetSearch action', () => {
    it('clears all search/result state', () => {
      // GIVEN - a store with search data
      const store = useScoutStore()
      const mockSearchResult: ScoutSearchResult = {
        run_id: 'run-123',
        status: 'complete',
        results: [
          {
            repo: 'facebook/react',
            fit_score: 85,
            reason: 'Great for learning React patterns',
            contributions: ['Add tests', 'Fix bugs'],
            reject: false,
            reject_reason: null
          }
        ],
        repos: [
          {
            github_id: 10270250,
            owner: 'facebook',
            name: 'react',
            url: 'https://github.com/facebook/react',
            description: 'A JavaScript library for building user interfaces',
            primary_language: 'JavaScript',
            languages: ['JavaScript'],
            star_count: 200000,
            fork_count: 40000,
            open_issue_count: 500,
            topics: ['react', 'javascript'],
            license: 'MIT',
            pushed_at: '2026-02-14T00:00:00Z',
            created_at: '2013-05-24T00:00:00Z',
            good_first_issue_count: 10,
            help_wanted_count: 5
          }
        ],
        warnings: ['Warning'],
        total_discovered: 50,
        total_filtered: 10,
        total_analyzed: 5
      }
      store.setSearchResult(mockSearchResult)
      store.currentRunId = 'run-123'
      store.searchPhase = 'analyze'
      store.statusMessage = 'Analyzing...'
      store.isSearching = true
      store.error = 'Some error'

      // WHEN - resetting search
      store.resetSearch()

      // THEN - all search/result state is cleared
      expect(store.currentRunId).toBeNull()
      expect(store.searchStatus).toBeNull()
      expect(store.searchPhase).toBeNull()
      expect(store.statusMessage).toBe('')
      expect(store.isSearching).toBe(false)
      expect(store.results).toEqual([])
      expect(store.repos).toEqual([])
      expect(store.warnings).toEqual([])
      expect(store.error).toBeNull()
      expect(store.totalDiscovered).toBe(0)
      expect(store.totalFiltered).toBe(0)
      expect(store.totalAnalyzed).toBe(0)
    })

  })
})
