import { ref } from 'vue'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'theme'
const DEFAULT_THEME: Theme = 'dark'

const theme = ref<Theme>(DEFAULT_THEME)

/**
 * Safely persist theme to localStorage.
 * Handles QuotaExceededError in private browsing or full storage.
 */
function persistTheme(themeValue: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, themeValue)
  } catch (e) {
    console.warn('Failed to save theme preference:', e)
  }
}

/**
 * Composable for managing theme state with localStorage persistence.
 *
 * Uses a singleton pattern - theme state is shared across all components.
 * Theme is initialized by inline script in index.html to prevent flash.
 */
export function useTheme() {
  /**
   * Sync Vue reactive state from current DOM attribute.
   * Falls back to localStorage if DOM attribute not set yet.
   */
  function syncFromDom(): void {
    const currentTheme = document.documentElement.getAttribute('data-theme') as Theme | null
    if (currentTheme === 'light' || currentTheme === 'dark') {
      theme.value = currentTheme
    } else {
      // Fallback: read from localStorage if DOM not initialized yet
      try {
        const saved = localStorage.getItem(STORAGE_KEY) as Theme | null
        theme.value = saved === 'light' || saved === 'dark' ? saved : DEFAULT_THEME
      } catch {
        theme.value = DEFAULT_THEME
      }
    }
  }

  /**
   * Toggle between light and dark themes
   */
  function toggleTheme(): void {
    const newTheme: Theme = theme.value === 'dark' ? 'light' : 'dark'
    theme.value = newTheme
    applyTheme(newTheme)
    persistTheme(newTheme)
  }

  /**
   * Set a specific theme
   */
  function setTheme(newTheme: Theme): void {
    theme.value = newTheme
    applyTheme(newTheme)
    persistTheme(newTheme)
  }

  /**
   * Apply theme to document element
   */
  function applyTheme(themeValue: Theme): void {
    document.documentElement.setAttribute('data-theme', themeValue)
  }

  return { theme, syncFromDom, toggleTheme, setTheme }
}
