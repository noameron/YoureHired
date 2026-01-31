import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { ref } from 'vue'
import ThemeToggle from '../ThemeToggle.vue'
import type { Theme } from '@/composables/useTheme'

// Mock the useTheme composable
const mockTheme = ref<Theme>('dark')
const mockToggleTheme = vi.fn()

vi.mock('@/composables/useTheme', () => ({
  useTheme: () => ({
    theme: mockTheme,
    toggleTheme: mockToggleTheme
  })
}))

describe('ThemeToggle', () => {
  let wrapper: VueWrapper

  beforeEach(() => {
    vi.clearAllMocks()
    mockTheme.value = 'dark'
  })

  describe('rendering', () => {
    it('renders toggle button with class "theme-toggle"', () => {
      // GIVEN - the component is mounted
      wrapper = mount(ThemeToggle)

      // THEN - button with correct class exists
      const button = wrapper.find('button')
      expect(button.exists()).toBe(true)
      expect(button.classes()).toContain('theme-toggle')
    })

    it('renders button with type "button"', () => {
      // GIVEN - the component is mounted
      wrapper = mount(ThemeToggle)

      // THEN - button has correct type attribute
      const button = wrapper.find('button')
      expect(button.attributes('type')).toBe('button')
    })
  })

  describe('icon visibility', () => {
    it('displays sun icon (circle element) when in dark mode', () => {
      // GIVEN - theme is set to dark mode
      mockTheme.value = 'dark'
      wrapper = mount(ThemeToggle)

      // WHEN - checking for sun icon elements
      const circles = wrapper.findAll('circle')
      const paths = wrapper.findAll('path')

      // THEN - sun icon (circle) is visible, moon icon (path) is not
      expect(circles.length).toBeGreaterThan(0)
      expect(paths.length).toBe(0)
    })

    it('displays moon icon (path element) when in light mode', () => {
      // GIVEN - theme is set to light mode
      mockTheme.value = 'light'
      wrapper = mount(ThemeToggle)

      // WHEN - checking for moon icon elements
      const paths = wrapper.findAll('path')
      const circles = wrapper.findAll('circle')

      // THEN - moon icon (path) is visible, sun icon (circle) is not
      expect(paths.length).toBeGreaterThan(0)
      expect(circles.length).toBe(0)
    })

    it('sun icon has correct SVG attributes', () => {
      // GIVEN - theme is set to dark mode
      mockTheme.value = 'dark'
      wrapper = mount(ThemeToggle)

      // WHEN - accessing the SVG element
      const svg = wrapper.find('svg')

      // THEN - sun icon SVG has correct attributes
      expect(svg.classes()).toContain('theme-icon')
      expect(svg.attributes('viewBox')).toBe('0 0 24 24')
      expect(svg.attributes('fill')).toBe('none')
      expect(svg.attributes('stroke')).toBe('currentColor')
    })

    it('moon icon has correct SVG attributes', () => {
      // GIVEN - theme is set to light mode
      mockTheme.value = 'light'
      wrapper = mount(ThemeToggle)

      // WHEN - accessing the SVG element
      const svg = wrapper.find('svg')

      // THEN - moon icon SVG has correct attributes
      expect(svg.classes()).toContain('theme-icon')
      expect(svg.attributes('viewBox')).toBe('0 0 24 24')
      expect(svg.attributes('fill')).toBe('none')
      expect(svg.attributes('stroke')).toBe('currentColor')
    })
  })

  describe('click interaction', () => {
    it('calls toggleTheme when button is clicked', async () => {
      // GIVEN - the component is mounted
      wrapper = mount(ThemeToggle)

      // WHEN - clicking the button
      await wrapper.find('button').trigger('click')

      // THEN - toggleTheme is called once
      expect(mockToggleTheme).toHaveBeenCalledOnce()
    })

    it('calls toggleTheme multiple times on multiple clicks', async () => {
      // GIVEN - the component is mounted
      wrapper = mount(ThemeToggle)

      // WHEN - clicking the button three times
      const button = wrapper.find('button')
      await button.trigger('click')
      await button.trigger('click')
      await button.trigger('click')

      // THEN - toggleTheme is called three times
      expect(mockToggleTheme).toHaveBeenCalledTimes(3)
    })
  })

  describe('accessibility', () => {
    it('has correct aria-label "Switch to light mode" when in dark mode', () => {
      // GIVEN - theme is set to dark mode
      mockTheme.value = 'dark'
      wrapper = mount(ThemeToggle)

      // WHEN - checking the aria-label
      const button = wrapper.find('button')

      // THEN - aria-label indicates switching to light mode
      expect(button.attributes('aria-label')).toBe('Switch to light mode')
    })

    it('has correct aria-label "Switch to dark mode" when in light mode', () => {
      // GIVEN - theme is set to light mode
      mockTheme.value = 'light'
      wrapper = mount(ThemeToggle)

      // WHEN - checking the aria-label
      const button = wrapper.find('button')

      // THEN - aria-label indicates switching to dark mode
      expect(button.attributes('aria-label')).toBe('Switch to dark mode')
    })

    it.each([
      { theme: 'dark' as Theme, expectedLabel: 'Switch to light mode' },
      { theme: 'light' as Theme, expectedLabel: 'Switch to dark mode' }
    ])('aria-label is $expectedLabel when theme is $theme', ({ theme, expectedLabel }) => {
      // GIVEN - theme is set to specific value
      mockTheme.value = theme
      wrapper = mount(ThemeToggle)

      // THEN - aria-label matches expected value
      const button = wrapper.find('button')
      expect(button.attributes('aria-label')).toBe(expectedLabel)
    })
  })

  describe('reactive theme updates', () => {
    it('updates icon when theme changes from dark to light', async () => {
      // GIVEN - component mounted in dark mode
      mockTheme.value = 'dark'
      wrapper = mount(ThemeToggle)

      // WHEN - theme changes to light
      mockTheme.value = 'light'
      await wrapper.vm.$nextTick()

      // THEN - moon icon is now visible
      expect(wrapper.findAll('path').length).toBeGreaterThan(0)
      expect(wrapper.findAll('circle').length).toBe(0)
    })

    it('updates icon when theme changes from light to dark', async () => {
      // GIVEN - component mounted in light mode
      mockTheme.value = 'light'
      wrapper = mount(ThemeToggle)

      // WHEN - theme changes to dark
      mockTheme.value = 'dark'
      await wrapper.vm.$nextTick()

      // THEN - sun icon is now visible
      expect(wrapper.findAll('circle').length).toBeGreaterThan(0)
      expect(wrapper.findAll('path').length).toBe(0)
    })

    it('updates aria-label when theme changes', async () => {
      // GIVEN - component mounted in dark mode
      mockTheme.value = 'dark'
      wrapper = mount(ThemeToggle)

      // WHEN - theme changes to light
      mockTheme.value = 'light'
      await wrapper.vm.$nextTick()

      // THEN - aria-label updates accordingly
      expect(wrapper.find('button').attributes('aria-label')).toBe('Switch to dark mode')
    })
  })

  describe('edge cases', () => {
    it('does not crash when toggleTheme is undefined', async () => {
      // GIVEN - useTheme returns undefined toggleTheme (defensive test)
      // This should not happen in production, but tests defensive coding
      // @ts-expect-error Testing undefined toggleTheme - defensive edge case
      vi.mocked(mockToggleTheme).mockImplementation(undefined)
      wrapper = mount(ThemeToggle)

      // WHEN - attempting to click (if toggleTheme was optional)
      // THEN - component still renders
      expect(wrapper.find('button').exists()).toBe(true)
    })

    it('renders only one SVG at a time', () => {
      // GIVEN - component mounted in dark mode
      mockTheme.value = 'dark'
      wrapper = mount(ThemeToggle)

      // THEN - only one SVG is present
      expect(wrapper.findAll('svg').length).toBe(1)
    })

    it('sun icon circle has correct center coordinates', () => {
      // GIVEN - theme is dark mode (sun icon visible)
      mockTheme.value = 'dark'
      wrapper = mount(ThemeToggle)

      // WHEN - accessing the circle element
      const circle = wrapper.find('circle')

      // THEN - circle has correct center coordinates and radius
      expect(circle.attributes('cx')).toBe('12')
      expect(circle.attributes('cy')).toBe('12')
      expect(circle.attributes('r')).toBe('5')
    })

    it('moon icon path has correct d attribute', () => {
      // GIVEN - theme is light mode (moon icon visible)
      mockTheme.value = 'light'
      wrapper = mount(ThemeToggle)

      // WHEN - accessing the path element
      const path = wrapper.find('path')

      // THEN - path has correct d attribute for moon shape
      expect(path.attributes('d')).toBe('M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z')
    })
  })
})
