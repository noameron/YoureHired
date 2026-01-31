import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FeedbackCard from '../FeedbackCard.vue'
import type { SolutionFeedback } from '@/services/types'

// Mock feedback data for testing
const createMockFeedback = (overrides?: Partial<SolutionFeedback>): SolutionFeedback => ({
  score: 7.5,
  strengths: [
    {
      title: 'Clean code structure',
      description: 'Well organized and readable code with proper separation of concerns.'
    }
  ],
  improvements: [
    {
      title: 'Error handling',
      description: 'Missing error handling for async operations.',
      suggestion: 'Add try/catch blocks around async calls to handle potential failures.'
    }
  ],
  summary_for_next_drill: 'Focus on error handling and edge cases.',
  ...overrides
})

// Helper to mount component with props
function mountFeedbackCard(props?: { feedback?: SolutionFeedback | null; isLoading?: boolean }) {
  return mount(FeedbackCard, { props })
}

describe('FeedbackCard', () => {
  describe('loading state', () => {
    it('shows spinner when isLoading is true', () => {
      // GIVEN - loading state is active
      const wrapper = mountFeedbackCard({ isLoading: true })

      // THEN - spinner element is visible
      expect(wrapper.find('.spinner').exists()).toBe(true)
    })

    it('shows evaluation message when isLoading is true', () => {
      // GIVEN - loading state is active
      const wrapper = mountFeedbackCard({ isLoading: true })

      // THEN - evaluation message is displayed
      expect(wrapper.text()).toContain('Evaluating your solution...')
    })

    it('does not show feedback content when isLoading is true', () => {
      // GIVEN - loading state is active with feedback provided
      const wrapper = mountFeedbackCard({
        isLoading: true,
        feedback: createMockFeedback()
      })

      // THEN - feedback content is not rendered
      expect(wrapper.find('.score-header').exists()).toBe(false)
      expect(wrapper.find('.feedback-section').exists()).toBe(false)
    })

    it('hides loading state when isLoading is false', () => {
      // GIVEN - loading state is inactive
      const wrapper = mountFeedbackCard({
        isLoading: false,
        feedback: createMockFeedback()
      })

      // THEN - loading elements are not visible
      expect(wrapper.find('.loading-state').exists()).toBe(false)
      expect(wrapper.find('.spinner').exists()).toBe(false)
    })
  })

  describe('empty state', () => {
    it('handles null feedback gracefully', () => {
      // GIVEN - feedback is null
      const wrapper = mountFeedbackCard({ feedback: null })

      // THEN - no error is thrown and component renders empty
      expect(wrapper.find('.feedback-card').exists()).toBe(true)
      expect(wrapper.find('.score-header').exists()).toBe(false)
    })

    it('handles undefined feedback gracefully', () => {
      // GIVEN - feedback is undefined
      const wrapper = mountFeedbackCard({ feedback: undefined })

      // THEN - no error is thrown and component renders empty
      expect(wrapper.find('.feedback-card').exists()).toBe(true)
      expect(wrapper.find('.score-header').exists()).toBe(false)
    })

    it('handles missing isLoading prop gracefully', () => {
      // GIVEN - isLoading prop is not provided
      const wrapper = mountFeedbackCard({ feedback: createMockFeedback() })

      // THEN - component renders feedback without loading state
      expect(wrapper.find('.loading-state').exists()).toBe(false)
      expect(wrapper.find('.score-header').exists()).toBe(true)
    })
  })

  describe('score display', () => {
    describe('score badge colors', () => {
      it.each([
        { score: 10, expectedClass: 'good', description: 'perfect score' },
        { score: 9, expectedClass: 'good', description: 'exceptional score' },
        { score: 7.5, expectedClass: 'good', description: 'good score at boundary' },
        { score: 7, expectedClass: 'good', description: 'good score minimum' },
        { score: 6.9, expectedClass: 'adequate', description: 'adequate score high' },
        { score: 6, expectedClass: 'adequate', description: 'adequate score mid' },
        { score: 5, expectedClass: 'adequate', description: 'adequate score minimum' },
        { score: 4.9, expectedClass: 'needs-work', description: 'needs work high' },
        { score: 3, expectedClass: 'needs-work', description: 'needs work mid' },
        { score: 0, expectedClass: 'needs-work', description: 'needs work minimum' }
      ])('applies $expectedClass class for score $score ($description)', ({ score, expectedClass }) => {
        // GIVEN - feedback with specific score
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({ score })
        })

        // THEN - correct color class is applied
        const scoreBadge = wrapper.find('.score-badge')
        expect(scoreBadge.classes()).toContain(expectedClass)
      })
    })

    describe('score labels', () => {
      it.each([
        { score: 10, expectedLabel: 'Exceptional' },
        { score: 9, expectedLabel: 'Exceptional' },
        { score: 8.9, expectedLabel: 'Good' },
        { score: 7.5, expectedLabel: 'Good' },
        { score: 7, expectedLabel: 'Good' },
        { score: 6.9, expectedLabel: 'Adequate' },
        { score: 5.5, expectedLabel: 'Adequate' },
        { score: 5, expectedLabel: 'Adequate' },
        { score: 4.9, expectedLabel: 'Needs Work' },
        { score: 3.5, expectedLabel: 'Needs Work' },
        { score: 3, expectedLabel: 'Needs Work' },
        { score: 2.9, expectedLabel: 'Incomplete' },
        { score: 1, expectedLabel: 'Incomplete' },
        { score: 0, expectedLabel: 'Incomplete' }
      ])('displays "$expectedLabel" for score $score', ({ score, expectedLabel }) => {
        // GIVEN - feedback with specific score
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({ score })
        })

        // THEN - correct label is displayed
        expect(wrapper.find('.score-label').text()).toBe(expectedLabel)
      })
    })

    it('displays score value with one decimal place', () => {
      // GIVEN - feedback with score
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ score: 8.456 })
      })

      // THEN - score is formatted to one decimal
      expect(wrapper.find('.score-value').text()).toBe('8.5')
    })

    it('displays score maximum value', () => {
      // GIVEN - feedback with any score
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ score: 7.5 })
      })

      // THEN - maximum score is shown
      expect(wrapper.find('.score-max').text()).toBe('/10')
    })

    it('renders Feedback header', () => {
      // GIVEN - feedback is provided
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback()
      })

      // THEN - header is rendered
      expect(wrapper.find('.score-header h2').text()).toBe('Feedback')
    })
  })

  describe('strengths section', () => {
    it('displays strengths section when strengths array has items', () => {
      // GIVEN - feedback with strengths
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          strengths: [
            { title: 'Good testing', description: 'Comprehensive test coverage' }
          ]
        })
      })

      // THEN - strengths section is visible
      expect(wrapper.find('.strengths-title').exists()).toBe(true)
      expect(wrapper.find('.strengths-title').text()).toContain('Strengths')
    })

    it('displays strength count in section title', () => {
      // GIVEN - feedback with multiple strengths
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          strengths: [
            { title: 'Strength 1', description: 'Desc 1' },
            { title: 'Strength 2', description: 'Desc 2' },
            { title: 'Strength 3', description: 'Desc 3' }
          ]
        })
      })

      // THEN - count is shown in title
      expect(wrapper.find('.strengths-title').text()).toContain('(3)')
    })

    it('does not display strengths section when array is empty', () => {
      // GIVEN - feedback with empty strengths array
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ strengths: [] })
      })

      // THEN - strengths section is not rendered
      expect(wrapper.find('.strengths-title').exists()).toBe(false)
    })

    it('renders all strength items', () => {
      // GIVEN - feedback with multiple strengths
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          strengths: [
            { title: 'Strength 1', description: 'Desc 1' },
            { title: 'Strength 2', description: 'Desc 2' }
          ]
        })
      })

      // THEN - all strength titles are rendered
      const items = wrapper.findAll('.strengths-title')[0]?.element.parentElement?.querySelectorAll('.feedback-item')
      expect(items?.length).toBe(2)
      expect(wrapper.text()).toContain('Strength 1')
      expect(wrapper.text()).toContain('Strength 2')
    })

    it('displays strength icon with correct styling', () => {
      // GIVEN - feedback with strengths
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          strengths: [{ title: 'Test', description: 'Desc' }]
        })
      })

      // THEN - icon has correct classes
      const icon = wrapper.find('.strengths-icon')
      expect(icon.exists()).toBe(true)
      expect(icon.text()).toBe('+')
    })
  })

  describe('improvements section', () => {
    it('displays improvements section when improvements array has items', () => {
      // GIVEN - feedback with improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          improvements: [
            {
              title: 'Better error handling',
              description: 'Add error boundaries',
              suggestion: 'Use try/catch'
            }
          ]
        })
      })

      // THEN - improvements section is visible
      expect(wrapper.find('.improvements-title').exists()).toBe(true)
      expect(wrapper.find('.improvements-title').text()).toContain('Areas for Improvement')
    })

    it('displays improvements count in section title', () => {
      // GIVEN - feedback with multiple improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          improvements: [
            { title: 'Imp 1', description: 'Desc 1', suggestion: 'Sug 1' },
            { title: 'Imp 2', description: 'Desc 2', suggestion: 'Sug 2' }
          ]
        })
      })

      // THEN - count is shown in title
      expect(wrapper.find('.improvements-title').text()).toContain('(2)')
    })

    it('does not display improvements section when array is empty', () => {
      // GIVEN - feedback with empty improvements array
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ improvements: [] })
      })

      // THEN - improvements section is not rendered
      expect(wrapper.find('.improvements-title').exists()).toBe(false)
    })

    it('renders all improvement items', () => {
      // GIVEN - feedback with multiple improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          improvements: [
            { title: 'Improvement 1', description: 'Desc 1', suggestion: 'Sug 1' },
            { title: 'Improvement 2', description: 'Desc 2', suggestion: 'Sug 2' }
          ]
        })
      })

      // THEN - all improvement titles are rendered
      expect(wrapper.text()).toContain('Improvement 1')
      expect(wrapper.text()).toContain('Improvement 2')
    })

    it('displays improvement icon with correct styling', () => {
      // GIVEN - feedback with improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          improvements: [
            { title: 'Test', description: 'Desc', suggestion: 'Sug' }
          ]
        })
      })

      // THEN - icon has correct classes
      const icon = wrapper.find('.improvements-icon')
      expect(icon.exists()).toBe(true)
      expect(icon.text()).toBe('!')
    })
  })

  describe('expandable items functionality', () => {
    describe('strengths expansion', () => {
      it('starts with strength description collapsed', () => {
        // GIVEN - feedback with strengths
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            strengths: [
              { title: 'Test Strength', description: 'Hidden description' }
            ]
          })
        })

        // THEN - description is not visible initially
        const content = wrapper.find('.feedback-section .item-content')
        expect(content.isVisible()).toBe(false)
      })

      it('expands strength description when toggle button is clicked', async () => {
        // GIVEN - feedback with strengths
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            strengths: [
              { title: 'Test Strength', description: 'Now visible description' }
            ]
          })
        })

        // WHEN - toggle button is clicked
        const toggleButton = wrapper.find('.strengths-title').element.parentElement?.querySelector('.item-toggle')
        await toggleButton?.dispatchEvent(new Event('click'))
        await wrapper.vm.$nextTick()

        // THEN - description becomes visible
        const content = wrapper.find('.item-content')
        expect(content.isVisible()).toBe(true)
        expect(content.text()).toContain('Now visible description')
      })

      it('collapses strength description when toggle button is clicked again', async () => {
        // GIVEN - feedback with expanded strength
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            strengths: [
              { title: 'Test Strength', description: 'Toggle me' }
            ]
          })
        })

        const section = wrapper.find('.strengths-title').element.parentElement
        const toggleButton = section?.querySelector('.item-toggle') as HTMLElement

        // WHEN - toggle button is clicked twice
        await toggleButton.click()
        await wrapper.vm.$nextTick()
        await toggleButton.click()
        await wrapper.vm.$nextTick()

        // THEN - description is hidden again
        const content = wrapper.find('.item-content')
        expect(content.isVisible()).toBe(false)
      })

      it('updates chevron icon when strength is expanded', async () => {
        // GIVEN - feedback with strengths
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            strengths: [
              { title: 'Test', description: 'Desc' }
            ]
          })
        })

        const section = wrapper.find('.strengths-title').element.parentElement
        const toggleButton = section?.querySelector('.item-toggle') as HTMLElement
        const chevron = section?.querySelector('.item-chevron')

        // WHEN - initially collapsed
        // THEN - shows right arrow
        expect(chevron?.textContent).toBe('▶')

        // WHEN - expanded
        await toggleButton.click()
        await wrapper.vm.$nextTick()

        // THEN - shows down arrow
        expect(chevron?.textContent).toBe('▼')
      })

      it('adds expanded class to toggle button when strength is expanded', async () => {
        // GIVEN - feedback with strengths
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            strengths: [
              { title: 'Test', description: 'Desc' }
            ]
          })
        })

        const section = wrapper.find('.strengths-title').element.parentElement
        const toggleButton = section?.querySelector('.item-toggle') as HTMLElement

        // WHEN - expanded
        await toggleButton.click()
        await wrapper.vm.$nextTick()

        // THEN - has expanded class
        expect(toggleButton.classList.contains('expanded')).toBe(true)
      })
    })

    describe('improvements expansion', () => {
      it('starts with improvement content collapsed', () => {
        // GIVEN - feedback with improvements
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            improvements: [
              {
                title: 'Test Improvement',
                description: 'Hidden description',
                suggestion: 'Hidden suggestion'
              }
            ]
          })
        })

        // THEN - content is not visible initially
        const content = wrapper.find('.improvements-title').element.parentElement?.querySelector('.item-content')
        expect(content?.getAttribute('style')).toContain('display: none')
      })

      it('expands improvement content when toggle button is clicked', async () => {
        // GIVEN - feedback with improvements
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            improvements: [
              {
                title: 'Test Improvement',
                description: 'Now visible description',
                suggestion: 'Now visible suggestion'
              }
            ]
          })
        })

        const section = wrapper.find('.improvements-title').element.parentElement
        const toggleButton = section?.querySelector('.item-toggle') as HTMLElement

        // WHEN - toggle button is clicked
        await toggleButton.click()
        await wrapper.vm.$nextTick()

        // THEN - content becomes visible
        const content = section?.querySelector('.item-content')
        expect(content?.getAttribute('style')).not.toContain('display: none')
        expect(content?.textContent).toContain('Now visible description')
        expect(content?.textContent).toContain('Now visible suggestion')
      })

      it('displays both description and suggestion when expanded', async () => {
        // GIVEN - feedback with improvements
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            improvements: [
              {
                title: 'Error Handling',
                description: 'Missing try/catch blocks',
                suggestion: 'Add error boundaries'
              }
            ]
          })
        })

        const section = wrapper.find('.improvements-title').element.parentElement
        const toggleButton = section?.querySelector('.item-toggle') as HTMLElement

        // WHEN - expanded
        await toggleButton.click()
        await wrapper.vm.$nextTick()

        // THEN - both description and suggestion are shown
        expect(wrapper.text()).toContain('Missing try/catch blocks')
        expect(wrapper.text()).toContain('Suggestion:')
        expect(wrapper.text()).toContain('Add error boundaries')
      })

      it('collapses improvement content when toggle button is clicked again', async () => {
        // GIVEN - feedback with improvements
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            improvements: [
              {
                title: 'Test',
                description: 'Desc',
                suggestion: 'Sug'
              }
            ]
          })
        })

        const section = wrapper.find('.improvements-title').element.parentElement
        const toggleButton = section?.querySelector('.item-toggle') as HTMLElement

        // WHEN - toggle button is clicked twice
        await toggleButton.click()
        await wrapper.vm.$nextTick()
        await toggleButton.click()
        await wrapper.vm.$nextTick()

        // THEN - content is hidden again
        const content = section?.querySelector('.item-content')
        expect(content?.getAttribute('style')).toContain('display: none')
      })
    })

    describe('independent expansion state', () => {
      it('expands multiple strengths independently', async () => {
        // GIVEN - feedback with multiple strengths
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            strengths: [
              { title: 'Strength 1', description: 'Desc 1' },
              { title: 'Strength 2', description: 'Desc 2' }
            ]
          })
        })

        const section = wrapper.find('.strengths-title').element.parentElement
        const toggleButtons = section?.querySelectorAll('.item-toggle') as NodeListOf<HTMLElement>

        // WHEN - first item is expanded
        await toggleButtons[0].click()
        await wrapper.vm.$nextTick()

        // THEN - only first item is expanded
        const contents = section?.querySelectorAll('.item-content') as NodeListOf<HTMLElement>
        expect(contents[0].style.display).not.toBe('none')
        expect(contents[1].style.display).toBe('none')

        // WHEN - second item is also expanded
        await toggleButtons[1].click()
        await wrapper.vm.$nextTick()

        // THEN - both items are expanded
        expect(contents[0].style.display).not.toBe('none')
        expect(contents[1].style.display).not.toBe('none')
      })

      it('expands multiple improvements independently', async () => {
        // GIVEN - feedback with multiple improvements
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            improvements: [
              { title: 'Imp 1', description: 'Desc 1', suggestion: 'Sug 1' },
              { title: 'Imp 2', description: 'Desc 2', suggestion: 'Sug 2' }
            ]
          })
        })

        const section = wrapper.find('.improvements-title').element.parentElement
        const toggleButtons = section?.querySelectorAll('.item-toggle') as NodeListOf<HTMLElement>

        // WHEN - first item is expanded
        await toggleButtons[0].click()
        await wrapper.vm.$nextTick()

        // THEN - only first item is expanded
        const contents = section?.querySelectorAll('.item-content') as NodeListOf<HTMLElement>
        expect(contents[0].style.display).not.toBe('none')
        expect(contents[1].style.display).toBe('none')
      })

      it('resets expanded state when feedback changes', async () => {
        // GIVEN - feedback with expanded items
        const wrapper = mountFeedbackCard({
          feedback: createMockFeedback({
            strengths: [{ title: 'Strength 1', description: 'Desc 1' }]
          })
        })

        const section = wrapper.find('.strengths-title').element.parentElement
        const toggleButton = section?.querySelector('.item-toggle') as HTMLElement

        // WHEN - item is expanded
        await toggleButton.click()
        await wrapper.vm.$nextTick()

        // THEN - item is expanded
        const content = section?.querySelector('.item-content') as HTMLElement
        expect(content.style.display).not.toBe('none')

        // WHEN - feedback prop changes
        await wrapper.setProps({
          feedback: createMockFeedback({
            strengths: [{ title: 'New Strength', description: 'New Desc' }]
          })
        })
        await wrapper.vm.$nextTick()

        // THEN - expansion state is reset (new item is collapsed)
        const newContent = wrapper.find('.item-content').element as HTMLElement
        expect(newContent.style.display).toBe('none')
      })
    })
  })

  describe('practice weak areas button', () => {
    it('displays button when improvements exist', () => {
      // GIVEN - feedback with improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          improvements: [
            { title: 'Test', description: 'Desc', suggestion: 'Sug' }
          ]
        })
      })

      // THEN - practice button is visible
      expect(wrapper.find('.practice-weak-areas-btn').exists()).toBe(true)
      expect(wrapper.find('.practice-weak-areas-btn').text()).toBe('Practice Weak Areas')
    })

    it('does not display button when improvements array is empty', () => {
      // GIVEN - feedback with no improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ improvements: [] })
      })

      // THEN - practice button is not rendered
      expect(wrapper.find('.practice-weak-areas-btn').exists()).toBe(false)
    })

    it('emits practice-weak-areas event when button is clicked', async () => {
      // GIVEN - feedback with improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          improvements: [
            { title: 'Test', description: 'Desc', suggestion: 'Sug' }
          ]
        })
      })

      // WHEN - button is clicked
      await wrapper.find('.practice-weak-areas-btn').trigger('click')

      // THEN - event is emitted
      expect(wrapper.emitted('practice-weak-areas')).toBeTruthy()
      expect(wrapper.emitted('practice-weak-areas')?.length).toBe(1)
    })

    it('displays practice hint text', () => {
      // GIVEN - feedback with improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          improvements: [
            { title: 'Test', description: 'Desc', suggestion: 'Sug' }
          ]
        })
      })

      // THEN - hint text is displayed
      expect(wrapper.find('.practice-hint').exists()).toBe(true)
      expect(wrapper.find('.practice-hint').text()).toContain(
        'Generate a new drill focused on the areas you need to improve'
      )
    })

    it('does not display hint text when no improvements', () => {
      // GIVEN - feedback with no improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ improvements: [] })
      })

      // THEN - hint text is not rendered
      expect(wrapper.find('.practice-hint').exists()).toBe(false)
    })
  })

  describe('edge cases', () => {
    it('handles feedback with no strengths and no improvements', () => {
      // GIVEN - feedback with empty arrays
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          strengths: [],
          improvements: []
        })
      })

      // THEN - only score is shown, no sections or buttons
      expect(wrapper.find('.score-header').exists()).toBe(true)
      expect(wrapper.find('.strengths-title').exists()).toBe(false)
      expect(wrapper.find('.improvements-title').exists()).toBe(false)
      expect(wrapper.find('.practice-weak-areas-btn').exists()).toBe(false)
    })

    it('handles feedback with only strengths', () => {
      // GIVEN - feedback with only strengths
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          strengths: [{ title: 'Great work', description: 'Excellent code' }],
          improvements: []
        })
      })

      // THEN - strengths shown, no improvements or practice button
      expect(wrapper.find('.strengths-title').exists()).toBe(true)
      expect(wrapper.find('.improvements-title').exists()).toBe(false)
      expect(wrapper.find('.practice-weak-areas-btn').exists()).toBe(false)
    })

    it('handles feedback with only improvements', () => {
      // GIVEN - feedback with only improvements
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          strengths: [],
          improvements: [
            { title: 'Needs work', description: 'Fix this', suggestion: 'Do this' }
          ]
        })
      })

      // THEN - improvements shown with practice button, no strengths
      expect(wrapper.find('.strengths-title').exists()).toBe(false)
      expect(wrapper.find('.improvements-title').exists()).toBe(true)
      expect(wrapper.find('.practice-weak-areas-btn').exists()).toBe(true)
    })

    it('handles very long strength descriptions', () => {
      // GIVEN - feedback with very long description
      const longDescription = 'A'.repeat(1000)
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          strengths: [{ title: 'Test', description: longDescription }]
        })
      })

      const section = wrapper.find('.strengths-title').element.parentElement
      const toggleButton = section?.querySelector('.item-toggle') as HTMLElement

      // WHEN - expanded
      toggleButton.click()
      wrapper.vm.$nextTick()

      // THEN - description is rendered without error
      expect(wrapper.text()).toContain(longDescription)
    })

    it('handles very long improvement suggestions', () => {
      // GIVEN - feedback with very long suggestion
      const longSuggestion = 'B'.repeat(1000)
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          improvements: [
            {
              title: 'Test',
              description: 'Desc',
              suggestion: longSuggestion
            }
          ]
        })
      })

      const section = wrapper.find('.improvements-title').element.parentElement
      const toggleButton = section?.querySelector('.item-toggle') as HTMLElement

      // WHEN - expanded
      toggleButton.click()
      wrapper.vm.$nextTick()

      // THEN - suggestion is rendered without error
      expect(wrapper.text()).toContain(longSuggestion)
    })

    it('handles special characters in feedback text', () => {
      // GIVEN - feedback with special characters
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({
          strengths: [
            {
              title: 'Code & Style <tag>',
              description: 'Contains "quotes" and \'apostrophes\''
            }
          ]
        })
      })

      // THEN - special characters are rendered correctly
      expect(wrapper.text()).toContain('Code & Style <tag>')
      expect(wrapper.text()).toContain('Contains "quotes" and \'apostrophes\'')
    })

    it('handles boundary score of exactly 7.0', () => {
      // GIVEN - feedback with boundary score
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ score: 7.0 })
      })

      // THEN - classified as good
      const scoreBadge = wrapper.find('.score-badge')
      expect(scoreBadge.classes()).toContain('good')
      expect(wrapper.find('.score-label').text()).toBe('Good')
    })

    it('handles boundary score of exactly 5.0', () => {
      // GIVEN - feedback with boundary score
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ score: 5.0 })
      })

      // THEN - classified as adequate
      const scoreBadge = wrapper.find('.score-badge')
      expect(scoreBadge.classes()).toContain('adequate')
      expect(wrapper.find('.score-label').text()).toBe('Adequate')
    })

    it('handles maximum score of 10', () => {
      // GIVEN - feedback with perfect score
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ score: 10 })
      })

      // THEN - displays correctly
      expect(wrapper.find('.score-value').text()).toBe('10.0')
      expect(wrapper.find('.score-label').text()).toBe('Exceptional')
      expect(wrapper.find('.score-badge').classes()).toContain('good')
    })

    it('handles minimum score of 0', () => {
      // GIVEN - feedback with zero score
      const wrapper = mountFeedbackCard({
        feedback: createMockFeedback({ score: 0 })
      })

      // THEN - displays correctly
      expect(wrapper.find('.score-value').text()).toBe('0.0')
      expect(wrapper.find('.score-label').text()).toBe('Incomplete')
      expect(wrapper.find('.score-badge').classes()).toContain('needs-work')
    })
  })
})
