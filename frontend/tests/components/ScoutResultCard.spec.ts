import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ScoutResultCard from '@/components/ScoutResultCard.vue'
import type { AnalysisResult, RepoMetadata } from '@/types/scout'

const mockRepo: RepoMetadata = {
  github_id: 12345,
  owner: 'fastapi',
  name: 'fastapi',
  url: 'https://github.com/fastapi/fastapi',
  description: 'FastAPI framework, high performance',
  primary_language: 'Python',
  languages: ['Python', 'Shell'],
  star_count: 65000,
  fork_count: 5000,
  open_issue_count: 120,
  topics: ['python', 'api', 'web'],
  license: 'MIT',
  pushed_at: '2024-01-15T00:00:00Z',
  created_at: '2018-12-08T00:00:00Z',
  good_first_issue_count: 5,
  help_wanted_count: 10
}

const mockResult: AnalysisResult = {
  repo: 'fastapi/fastapi',
  fit_score: 8.5,
  reason: 'Great match for Python web developers',
  contributions: ['Fix documentation typos', 'Add new endpoint tests', 'Improve error handling'],
  reject: false,
  reject_reason: null
}

function mountCard(result: AnalysisResult = mockResult, repo: RepoMetadata = mockRepo) {
  return mount(ScoutResultCard, {
    props: { result, repo }
  })
}

describe('ScoutResultCard', () => {
  it('renders repo name as link with correct URL', () => {
    // GIVEN
    const wrapper = mountCard()

    // WHEN
    const link = wrapper.find('a')

    // THEN
    expect(link.exists()).toBe(true)
    expect(link.attributes('href')).toBe('https://github.com/fastapi/fastapi')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
    expect(link.text()).toBe('fastapi/fastapi')
  })

  it('renders score badge with correct value', () => {
    // GIVEN
    const wrapper = mountCard()

    // WHEN
    const scoreBadge = wrapper.find('[data-testid="score-badge"]')

    // THEN
    expect(scoreBadge.exists()).toBe(true)
    expect(scoreBadge.text()).toContain('8.5')
  })

  it.each([
    [10, 'score-green'],
    [8, 'score-green'],
    [7, 'score-yellow'],
    [5, 'score-yellow'],
    [4, 'score-red'],
    [0, 'score-red']
  ])('score badge has correct color class for score %d', (score, expectedClass) => {
    // GIVEN
    const result: AnalysisResult = { ...mockResult, fit_score: score }

    // WHEN
    const wrapper = mountCard(result)
    const scoreBadge = wrapper.find('[data-testid="score-badge"]')

    // THEN
    expect(scoreBadge.classes()).toContain(expectedClass)
  })

  it('renders contributions list', () => {
    // GIVEN
    const wrapper = mountCard()

    // WHEN
    const listItems = wrapper.findAll('li')

    // THEN
    expect(listItems).toHaveLength(3)
    expect(listItems[0].text()).toBe('Fix documentation typos')
    expect(listItems[1].text()).toBe('Add new endpoint tests')
    expect(listItems[2].text()).toBe('Improve error handling')
  })

  it('renders repo metadata', () => {
    // GIVEN
    const wrapper = mountCard()

    // WHEN
    const text = wrapper.text()

    // THEN
    expect(text).toContain('★ 65,000')
    expect(text).toContain('Python')
    expect(text).toContain('120 issues')
  })

  it('handles missing description gracefully', () => {
    // GIVEN
    const repo: RepoMetadata = { ...mockRepo, description: null }

    // WHEN / THEN
    expect(() => mountCard(mockResult, repo)).not.toThrow()
  })

  it('handles missing license gracefully', () => {
    // GIVEN
    const repo: RepoMetadata = { ...mockRepo, license: null }

    // WHEN
    const wrapper = mountCard(mockResult, repo)

    // THEN
    const metadataRow = wrapper.find('.metadata-row')
    expect(metadataRow.text()).not.toContain('MIT')
  })

  it('handles missing primary language gracefully', () => {
    // GIVEN
    const repo: RepoMetadata = { ...mockRepo, primary_language: null }

    // WHEN
    const wrapper = mountCard(mockResult, repo)

    // THEN
    const metadataRow = wrapper.find('.metadata-row')
    expect(metadataRow.text()).not.toContain('Python')
  })

  it('handles empty contributions array', () => {
    // GIVEN
    const result: AnalysisResult = { ...mockResult, contributions: [] }

    // WHEN
    const wrapper = mountCard(result)

    // THEN
    const contributionsList = wrapper.find('.contributions')
    expect(contributionsList.exists()).toBe(false)
  })
})
