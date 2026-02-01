import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { useTheme, type Theme } from '@/composables/useTheme'

describe('useTheme composable', () => {
  let localStorageMock: { [key: string]: string }
  let documentElement: HTMLElement

  beforeEach(() => {
    // Reset singleton theme state to default
    const { theme } = useTheme()
    theme.value = 'dark'

    // Mock localStorage
    localStorageMock = {}
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => localStorageMock[key] || null),
      setItem: vi.fn((key: string, value: string) => {
        localStorageMock[key] = value
      }),
      removeItem: vi.fn((key: string) => {
        delete localStorageMock[key]
      }),
      clear: vi.fn(() => {
        localStorageMock = {}
      })
    })

    // Mock document.documentElement
    documentElement = {
      getAttribute: vi.fn((_attr: string) => null),
      setAttribute: vi.fn()
    } as unknown as HTMLElement
    vi.stubGlobal('document', {
      documentElement
    })

    // Mock console.warn to suppress test noise
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('has theme initialized to dark by default', () => {
      // GIVEN - a fresh useTheme instance
      const { theme } = useTheme()

      // WHEN - accessing initial state
      // (no action needed)

      // THEN - theme is set to dark
      expect(theme.value).toBe('dark')
    })
  })

  describe('toggleTheme', () => {
    it('switches from dark to light', () => {
      // GIVEN - theme is dark
      const { theme, toggleTheme } = useTheme()
      theme.value = 'dark'

      // WHEN - toggling theme
      toggleTheme()

      // THEN - theme switches to light
      expect(theme.value).toBe('light')
    })

    it('switches from light to dark', () => {
      // GIVEN - theme is light
      const { theme, toggleTheme } = useTheme()
      theme.value = 'light'

      // WHEN - toggling theme
      toggleTheme()

      // THEN - theme switches to dark
      expect(theme.value).toBe('dark')
    })

    it('applies theme to document element when toggling', () => {
      // GIVEN - theme is dark
      const { toggleTheme } = useTheme()

      // WHEN - toggling theme
      toggleTheme()

      // THEN - data-theme attribute is set to light
      expect(documentElement.setAttribute).toHaveBeenCalledWith('data-theme', 'light')
    })

    it('persists theme to localStorage when toggling', () => {
      // GIVEN - theme is dark
      const { toggleTheme } = useTheme()

      // WHEN - toggling theme
      toggleTheme()

      // THEN - theme is saved to localStorage
      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'light')
      expect(localStorageMock['theme']).toBe('light')
    })
  })

  describe('setTheme', () => {
    it.each([
      { newTheme: 'light' as Theme, description: 'light' },
      { newTheme: 'dark' as Theme, description: 'dark' }
    ])('sets theme to $description', ({ newTheme }) => {
      // GIVEN - a useTheme instance
      const { theme, setTheme } = useTheme()

      // WHEN - setting theme to specified value
      setTheme(newTheme)

      // THEN - theme is updated
      expect(theme.value).toBe(newTheme)
    })

    it('applies theme to document element', () => {
      // GIVEN - a useTheme instance
      const { setTheme } = useTheme()

      // WHEN - setting theme to light
      setTheme('light')

      // THEN - data-theme attribute is set
      expect(documentElement.setAttribute).toHaveBeenCalledWith('data-theme', 'light')
    })

    it('persists theme to localStorage', () => {
      // GIVEN - a useTheme instance
      const { setTheme } = useTheme()

      // WHEN - setting theme to light
      setTheme('light')

      // THEN - theme is saved to localStorage
      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'light')
      expect(localStorageMock['theme']).toBe('light')
    })
  })

  describe('localStorage persistence', () => {
    it('handles QuotaExceededError gracefully', () => {
      // GIVEN - localStorage throws QuotaExceededError
      const quotaError = new DOMException('QuotaExceededError', 'QuotaExceededError')
      vi.mocked(localStorage.setItem).mockImplementation(() => {
        throw quotaError
      })
      const { setTheme } = useTheme()

      // WHEN - attempting to save theme
      setTheme('light')

      // THEN - error is caught and logged, theme is still applied to DOM
      expect(console.warn).toHaveBeenCalledWith('Failed to save theme preference:', quotaError)
      expect(documentElement.setAttribute).toHaveBeenCalledWith('data-theme', 'light')
    })

    it('handles generic localStorage errors gracefully', () => {
      // GIVEN - localStorage throws generic error
      const genericError = new Error('Storage unavailable')
      vi.mocked(localStorage.setItem).mockImplementation(() => {
        throw genericError
      })
      const { toggleTheme } = useTheme()

      // WHEN - attempting to toggle theme
      toggleTheme()

      // THEN - error is caught and logged
      expect(console.warn).toHaveBeenCalledWith('Failed to save theme preference:', genericError)
    })
  })

  describe('syncFromDom', () => {
    it('reads light theme from data-theme attribute', () => {
      // GIVEN - document element has data-theme="light"
      vi.mocked(documentElement.getAttribute).mockReturnValue('light')
      const { theme, syncFromDom } = useTheme()
      theme.value = 'dark' // Start with different value

      // WHEN - syncing from DOM
      syncFromDom()

      // THEN - theme is updated to match DOM attribute
      expect(documentElement.getAttribute).toHaveBeenCalledWith('data-theme')
      expect(theme.value).toBe('light')
    })

    it('reads dark theme from data-theme attribute', () => {
      // GIVEN - document element has data-theme="dark"
      vi.mocked(documentElement.getAttribute).mockReturnValue('dark')
      const { theme, syncFromDom } = useTheme()
      theme.value = 'light' // Start with different value

      // WHEN - syncing from DOM
      syncFromDom()

      // THEN - theme is updated to match DOM attribute
      expect(theme.value).toBe('dark')
    })

    it('falls back to localStorage when data-theme attribute not set', () => {
      // GIVEN - no data-theme attribute, but localStorage has "light"
      vi.mocked(documentElement.getAttribute).mockReturnValue(null)
      localStorageMock['theme'] = 'light'
      const { theme, syncFromDom } = useTheme()

      // WHEN - syncing from DOM
      syncFromDom()

      // THEN - theme is read from localStorage
      expect(localStorage.getItem).toHaveBeenCalledWith('theme')
      expect(theme.value).toBe('light')
    })

    it('falls back to default theme when both DOM and localStorage are empty', () => {
      // GIVEN - no data-theme attribute and no localStorage value
      vi.mocked(documentElement.getAttribute).mockReturnValue(null)
      const { theme, syncFromDom } = useTheme()
      theme.value = 'light' // Start with non-default value

      // WHEN - syncing from DOM
      syncFromDom()

      // THEN - theme is set to default (dark)
      expect(theme.value).toBe('dark')
    })

    it('ignores invalid data-theme attribute values', () => {
      // GIVEN - data-theme has invalid value, localStorage has "light"
      vi.mocked(documentElement.getAttribute).mockReturnValue('invalid-theme')
      localStorageMock['theme'] = 'light'
      const { theme, syncFromDom } = useTheme()

      // WHEN - syncing from DOM
      syncFromDom()

      // THEN - falls back to localStorage instead of using invalid value
      expect(theme.value).toBe('light')
    })

    it('ignores invalid localStorage values', () => {
      // GIVEN - no data-theme attribute, localStorage has invalid value
      vi.mocked(documentElement.getAttribute).mockReturnValue(null)
      localStorageMock['theme'] = 'invalid-theme'
      const { theme, syncFromDom } = useTheme()
      theme.value = 'light' // Start with non-default value

      // WHEN - syncing from DOM
      syncFromDom()

      // THEN - falls back to default theme
      expect(theme.value).toBe('dark')
    })

    it('handles localStorage access errors gracefully', () => {
      // GIVEN - no data-theme attribute and localStorage throws error
      vi.mocked(documentElement.getAttribute).mockReturnValue(null)
      vi.mocked(localStorage.getItem).mockImplementation(() => {
        throw new Error('Storage unavailable')
      })
      const { theme, syncFromDom } = useTheme()
      theme.value = 'light' // Start with non-default value

      // WHEN - syncing from DOM
      syncFromDom()

      // THEN - falls back to default theme without crashing
      expect(theme.value).toBe('dark')
    })
  })

  describe('singleton behavior', () => {
    it('shares theme state across multiple useTheme instances', () => {
      // GIVEN - two separate useTheme instances
      const instance1 = useTheme()
      const instance2 = useTheme()

      // WHEN - setting theme on one instance
      instance1.setTheme('light')

      // THEN - both instances reflect the same theme value
      expect(instance1.theme.value).toBe('light')
      expect(instance2.theme.value).toBe('light')
      expect(instance1.theme).toBe(instance2.theme) // Same ref object
    })
  })
})
