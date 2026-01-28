import { describe, it, expect, beforeEach } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import AgentCarousel from '../AgentCarousel.vue'
import type { AgentData } from '../AgentCarousel.vue'

describe('AgentCarousel', () => {
  const createAgents = (count: number): AgentData[] => {
    return Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      name: `Agent ${i + 1}`,
      status: 'pending' as const,
      output: null
    }))
  }

  describe('rendering', () => {
    it('renders carousel container', () => {
      // GIVEN - component is mounted with agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - carousel container exists
      expect(wrapper.find('.carousel-container').exists()).toBe(true)
    })

    it('renders carousel viewport', () => {
      // GIVEN - component is mounted with agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - carousel viewport exists
      expect(wrapper.find('.carousel-viewport').exists()).toBe(true)
    })

    it('renders correct number of slides', () => {
      // GIVEN - component is mounted with 3 agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - 3 slides are rendered
      const slides = wrapper.findAll('.carousel-slide')
      expect(slides.length).toBe(3)
    })

    it('renders AgentOutputCard for each agent', () => {
      // GIVEN - component is mounted with agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(2) }
      })

      // THEN - AgentOutputCard components are rendered
      const cards = wrapper.findAllComponents({ name: 'AgentOutputCard' })
      expect(cards.length).toBe(2)
    })

    it('renders navigation arrows', () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - both arrows exist
      expect(wrapper.find('.arrow-left').exists()).toBe(true)
      expect(wrapper.find('.arrow-right').exists()).toBe(true)
    })

    it('renders dot indicators for each slide', () => {
      // GIVEN - component is mounted with 4 agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(4) }
      })

      // THEN - 4 dot indicators exist
      const dots = wrapper.findAll('.dot')
      expect(dots.length).toBe(4)
    })
  })

  describe('initial state', () => {
    it('starts at first slide (index 0)', () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - first dot is active
      const dots = wrapper.findAll('.dot')
      expect(dots[0].classes()).toContain('active')
      expect(dots[1].classes()).not.toContain('active')
    })

    it('left arrow is disabled on first slide', () => {
      // GIVEN - component is mounted (starts at first slide)
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - left arrow is disabled
      const leftArrow = wrapper.find('.arrow-left')
      expect(leftArrow.attributes('disabled')).toBeDefined()
    })

    it('right arrow is enabled on first slide with multiple agents', () => {
      // GIVEN - component is mounted with multiple agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - right arrow is not disabled
      const rightArrow = wrapper.find('.arrow-right')
      expect(rightArrow.attributes('disabled')).toBeUndefined()
    })

    it('slide transform starts at 0%', () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - transform is translateX(0%)
      const slides = wrapper.find('.carousel-slides')
      expect(slides.attributes('style')).toContain('translateX(-0%)')
    })
  })

  describe('navigation: nextSlide', () => {
    it('advances to next slide when right arrow is clicked', async () => {
      // GIVEN - component is mounted at first slide
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // WHEN - clicking right arrow
      await wrapper.find('.arrow-right').trigger('click')

      // THEN - now on second slide
      const dots = wrapper.findAll('.dot')
      expect(dots[0].classes()).not.toContain('active')
      expect(dots[1].classes()).toContain('active')
    })

    it('updates transform when advancing', async () => {
      // GIVEN - component is mounted at first slide
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // WHEN - clicking right arrow
      await wrapper.find('.arrow-right').trigger('click')

      // THEN - transform is translateX(-100%)
      const slides = wrapper.find('.carousel-slides')
      expect(slides.attributes('style')).toContain('translateX(-100%)')
    })

    it('does not advance past last slide', async () => {
      // GIVEN - component is mounted at last slide
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(2) }
      })
      await wrapper.find('.arrow-right').trigger('click') // Go to slide 2 (index 1)

      // WHEN - clicking right arrow again
      await wrapper.find('.arrow-right').trigger('click')

      // THEN - still on last slide
      const dots = wrapper.findAll('.dot')
      expect(dots[1].classes()).toContain('active')
    })

    it('right arrow becomes disabled on last slide', async () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(2) }
      })

      // WHEN - navigating to last slide
      await wrapper.find('.arrow-right').trigger('click')

      // THEN - right arrow is disabled
      const rightArrow = wrapper.find('.arrow-right')
      expect(rightArrow.attributes('disabled')).toBeDefined()
    })
  })

  describe('navigation: prevSlide', () => {
    it('goes to previous slide when left arrow is clicked', async () => {
      // GIVEN - component is mounted and on second slide
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })
      await wrapper.find('.arrow-right').trigger('click') // Go to slide 2

      // WHEN - clicking left arrow
      await wrapper.find('.arrow-left').trigger('click')

      // THEN - back to first slide
      const dots = wrapper.findAll('.dot')
      expect(dots[0].classes()).toContain('active')
    })

    it('updates transform when going back', async () => {
      // GIVEN - on second slide
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })
      await wrapper.find('.arrow-right').trigger('click')

      // WHEN - clicking left arrow
      await wrapper.find('.arrow-left').trigger('click')

      // THEN - transform is back to translateX(-0%)
      const slides = wrapper.find('.carousel-slides')
      expect(slides.attributes('style')).toContain('translateX(-0%)')
    })

    it('does not go before first slide', async () => {
      // GIVEN - component is mounted at first slide
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // WHEN - clicking left arrow (already at first)
      await wrapper.find('.arrow-left').trigger('click')

      // THEN - still at first slide
      const dots = wrapper.findAll('.dot')
      expect(dots[0].classes()).toContain('active')
    })

    it('left arrow becomes enabled after moving from first slide', async () => {
      // GIVEN - component is on first slide (left disabled)
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })
      expect(wrapper.find('.arrow-left').attributes('disabled')).toBeDefined()

      // WHEN - navigating to next slide
      await wrapper.find('.arrow-right').trigger('click')

      // THEN - left arrow is now enabled
      expect(wrapper.find('.arrow-left').attributes('disabled')).toBeUndefined()
    })
  })

  describe('navigation: goToSlide (dot clicks)', () => {
    it('navigates to specific slide when dot is clicked', async () => {
      // GIVEN - component is mounted at first slide
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(4) }
      })

      // WHEN - clicking third dot (index 2)
      const dots = wrapper.findAll('.dot')
      await dots[2].trigger('click')

      // THEN - third slide is active
      expect(dots[2].classes()).toContain('active')
    })

    it('updates transform when jumping to slide', async () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(4) }
      })

      // WHEN - clicking third dot (index 2)
      await wrapper.findAll('.dot')[2].trigger('click')

      // THEN - transform is translateX(-200%)
      const slides = wrapper.find('.carousel-slides')
      expect(slides.attributes('style')).toContain('translateX(-200%)')
    })

    it('updates arrow disabled states when jumping', async () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // WHEN - clicking last dot
      await wrapper.findAll('.dot')[2].trigger('click')

      // THEN - left enabled, right disabled
      expect(wrapper.find('.arrow-left').attributes('disabled')).toBeUndefined()
      expect(wrapper.find('.arrow-right').attributes('disabled')).toBeDefined()
    })
  })

  describe('touch handling', () => {
    let wrapper: VueWrapper

    beforeEach(() => {
      wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })
    })

    it('responds to swipe left (advances slide)', async () => {
      // GIVEN - on first slide
      const viewport = wrapper.find('.carousel-viewport')

      // WHEN - simulating swipe left (start at 200, end at 100)
      await viewport.trigger('touchstart', {
        touches: [{ clientX: 200 }]
      })
      await viewport.trigger('touchmove', {
        touches: [{ clientX: 100 }]
      })
      await viewport.trigger('touchend')

      // THEN - advanced to second slide
      const dots = wrapper.findAll('.dot')
      expect(dots[1].classes()).toContain('active')
    })

    it('responds to swipe right (goes to previous slide)', async () => {
      // GIVEN - on second slide
      await wrapper.find('.arrow-right').trigger('click')
      const viewport = wrapper.find('.carousel-viewport')

      // WHEN - simulating swipe right (start at 100, end at 200)
      await viewport.trigger('touchstart', {
        touches: [{ clientX: 100 }]
      })
      await viewport.trigger('touchmove', {
        touches: [{ clientX: 200 }]
      })
      await viewport.trigger('touchend')

      // THEN - back to first slide
      const dots = wrapper.findAll('.dot')
      expect(dots[0].classes()).toContain('active')
    })

    it('ignores swipe below threshold (49px)', async () => {
      // GIVEN - on first slide
      const viewport = wrapper.find('.carousel-viewport')

      // WHEN - simulating small swipe (only 49px)
      await viewport.trigger('touchstart', {
        touches: [{ clientX: 200 }]
      })
      await viewport.trigger('touchmove', {
        touches: [{ clientX: 151 }]
      })
      await viewport.trigger('touchend')

      // THEN - still on first slide
      const dots = wrapper.findAll('.dot')
      expect(dots[0].classes()).toContain('active')
    })

    it('triggers navigation at exactly 50px threshold', async () => {
      // GIVEN - on first slide
      const viewport = wrapper.find('.carousel-viewport')

      // WHEN - simulating exactly 51px swipe (just over threshold)
      await viewport.trigger('touchstart', {
        touches: [{ clientX: 200 }]
      })
      await viewport.trigger('touchmove', {
        touches: [{ clientX: 149 }]
      })
      await viewport.trigger('touchend')

      // THEN - advanced to second slide
      const dots = wrapper.findAll('.dot')
      expect(dots[1].classes()).toContain('active')
    })

    it('does not swipe past first slide', async () => {
      // GIVEN - on first slide
      const viewport = wrapper.find('.carousel-viewport')

      // WHEN - swiping right (trying to go before first)
      await viewport.trigger('touchstart', {
        touches: [{ clientX: 100 }]
      })
      await viewport.trigger('touchmove', {
        touches: [{ clientX: 200 }]
      })
      await viewport.trigger('touchend')

      // THEN - still on first slide
      const dots = wrapper.findAll('.dot')
      expect(dots[0].classes()).toContain('active')
    })

    it('does not swipe past last slide', async () => {
      // GIVEN - on last slide
      await wrapper.findAll('.dot')[2].trigger('click')
      const viewport = wrapper.find('.carousel-viewport')

      // WHEN - swiping left (trying to go past last)
      await viewport.trigger('touchstart', {
        touches: [{ clientX: 200 }]
      })
      await viewport.trigger('touchmove', {
        touches: [{ clientX: 100 }]
      })
      await viewport.trigger('touchend')

      // THEN - still on last slide
      const dots = wrapper.findAll('.dot')
      expect(dots[2].classes()).toContain('active')
    })
  })

  describe('accessibility', () => {
    it('left arrow has aria-label "Previous agent"', () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - left arrow has correct aria-label
      expect(wrapper.find('.arrow-left').attributes('aria-label')).toBe('Previous agent')
    })

    it('right arrow has aria-label "Next agent"', () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - right arrow has correct aria-label
      expect(wrapper.find('.arrow-right').attributes('aria-label')).toBe('Next agent')
    })

    it('dots have aria-labels indicating agent number', () => {
      // GIVEN - component is mounted with 3 agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - dots have correct aria-labels
      const dots = wrapper.findAll('.dot')
      expect(dots[0].attributes('aria-label')).toBe('Go to agent 1')
      expect(dots[1].attributes('aria-label')).toBe('Go to agent 2')
      expect(dots[2].attributes('aria-label')).toBe('Go to agent 3')
    })

    it('active dot has aria-current="true"', () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // THEN - first dot has aria-current
      const dots = wrapper.findAll('.dot')
      expect(dots[0].attributes('aria-current')).toBe('true')
      expect(dots[1].attributes('aria-current')).toBeUndefined()
    })

    it('aria-current updates when navigating', async () => {
      // GIVEN - component is mounted
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(3) }
      })

      // WHEN - navigating to second slide
      await wrapper.find('.arrow-right').trigger('click')

      // THEN - second dot has aria-current
      const dots = wrapper.findAll('.dot')
      expect(dots[0].attributes('aria-current')).toBeUndefined()
      expect(dots[1].attributes('aria-current')).toBe('true')
    })
  })

  describe('edge cases', () => {
    it('handles single agent (no navigation needed)', () => {
      // GIVEN - component with single agent
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(1) }
      })

      // THEN - both arrows are disabled
      expect(wrapper.find('.arrow-left').attributes('disabled')).toBeDefined()
      expect(wrapper.find('.arrow-right').attributes('disabled')).toBeDefined()
    })

    it('renders single dot for single agent', () => {
      // GIVEN - component with single agent
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(1) }
      })

      // THEN - only one dot exists and is active
      const dots = wrapper.findAll('.dot')
      expect(dots.length).toBe(1)
      expect(dots[0].classes()).toContain('active')
    })

    it('handles empty agents array', () => {
      // GIVEN - component with no agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: [] }
      })

      // THEN - no slides or dots rendered
      expect(wrapper.findAll('.carousel-slide').length).toBe(0)
      expect(wrapper.findAll('.dot').length).toBe(0)
    })

    it('passes correct props to AgentOutputCard', () => {
      // GIVEN - agents with various statuses
      const agents: AgentData[] = [
        { id: 1, name: 'Agent One', status: 'running', output: 'Working...' },
        { id: 2, name: 'Agent Two', status: 'error', output: null, error: 'Failed' }
      ]
      const wrapper = mount(AgentCarousel, {
        props: { agents }
      })

      // THEN - props are passed correctly
      const cards = wrapper.findAllComponents({ name: 'AgentOutputCard' })
      expect(cards[0].props('name')).toBe('Agent One')
      expect(cards[0].props('status')).toBe('running')
      expect(cards[0].props('output')).toBe('Working...')
      expect(cards[1].props('name')).toBe('Agent Two')
      expect(cards[1].props('status')).toBe('error')
      expect(cards[1].props('error')).toBe('Failed')
    })

    it('handles many agents', () => {
      // GIVEN - component with many agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(10) }
      })

      // THEN - all slides and dots render
      expect(wrapper.findAll('.carousel-slide').length).toBe(10)
      expect(wrapper.findAll('.dot').length).toBe(10)
    })
  })

  describe('slide transform calculations', () => {
    it.each([
      { slideIndex: 0, expectedTransform: 'translateX(-0%)' },
      { slideIndex: 1, expectedTransform: 'translateX(-100%)' },
      { slideIndex: 2, expectedTransform: 'translateX(-200%)' },
      { slideIndex: 3, expectedTransform: 'translateX(-300%)' }
    ])('transform is $expectedTransform at slide index $slideIndex', async ({ slideIndex, expectedTransform }) => {
      // GIVEN - component with 4 agents
      const wrapper = mount(AgentCarousel, {
        props: { agents: createAgents(4) }
      })

      // WHEN - navigating to specific slide
      if (slideIndex > 0) {
        await wrapper.findAll('.dot')[slideIndex].trigger('click')
      }

      // THEN - transform is correct
      const slides = wrapper.find('.carousel-slides')
      expect(slides.attributes('style')).toContain(expectedTransform)
    })
  })
})
