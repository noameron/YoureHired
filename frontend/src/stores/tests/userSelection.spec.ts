import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserSelectionStore } from '../userSelection'

describe('userSelection store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('initial state', () => {
    it.each([
      { property: 'companyName', expected: '' },
      { property: 'role', expected: '' },
      { property: 'roleDescription', expected: null },
      { property: 'sessionId', expected: null }
    ])('has $property initialized to $expected', ({ property, expected }) => {
      // GIVEN - a fresh store instance
      const store = useUserSelectionStore()

      // WHEN - accessing initial state
      // (no action needed)

      // THEN - property has correct initial value
      expect(store[property as keyof typeof store]).toBe(expected)
    })
  })

  describe('setSelection action', () => {
    it('updates all store properties with provided selection data', () => {
      // GIVEN - a fresh store instance
      const store = useUserSelectionStore()

      // WHEN - setting selection with all fields
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: 'Senior position focusing on APIs',
        sessionId: 'session-uuid-12345'
      })

      // THEN - all properties are updated correctly
      expect(store.companyName).toBe('Test Corp')
      expect(store.role).toBe('backend_developer')
      expect(store.roleDescription).toBe('Senior position focusing on APIs')
      expect(store.sessionId).toBe('session-uuid-12345')
    })

    it.each([
      { roleDescription: null, label: 'null', expected: null },
      { roleDescription: undefined, label: 'undefined', expected: undefined },
      { roleDescription: 'Senior position', label: 'a string', expected: 'Senior position' }
    ])('handles roleDescription as $label correctly', ({ roleDescription, expected }) => {
      // GIVEN - a fresh store instance
      const store = useUserSelectionStore()

      // WHEN - setting selection with roleDescription as provided value
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: roleDescription as string | null,
        sessionId: 'abc-123'
      })

      // THEN - roleDescription is stored with the provided value
      expect(store.roleDescription).toBe(expected)
    })
  })

  describe('clearSelection action', () => {
    it('resets all store properties to initial state', () => {
      // GIVEN - a store with existing selection
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: 'Description',
        sessionId: 'abc-123'
      })

      // WHEN - clearing the selection
      store.clearSelection()

      // THEN - all properties are reset to initial values
      expect(store.companyName).toBe('')
      expect(store.role).toBe('')
      expect(store.roleDescription).toBeNull()
      expect(store.sessionId).toBeNull()
    })
  })

  describe('hasSelection getter', () => {
    it.each([
      {
        description: 'returns false when no selection made',
        setup: (store: ReturnType<typeof useUserSelectionStore>) => {
          // No setup needed - initial state
        },
        expected: false
      },
      {
        description: 'returns true when selection is set',
        setup: (store: ReturnType<typeof useUserSelectionStore>) => {
          store.setSelection({
            companyName: 'Test Corp',
            role: 'backend_developer',
            roleDescription: null,
            sessionId: 'abc-123'
          })
        },
        expected: true
      },
      {
        description: 'returns false after clearSelection',
        setup: (store: ReturnType<typeof useUserSelectionStore>) => {
          store.setSelection({
            companyName: 'Test Corp',
            role: 'backend_developer',
            roleDescription: null,
            sessionId: 'abc-123'
          })
          store.clearSelection()
        },
        expected: false
      }
    ])('$description', ({ setup, expected }) => {
      // GIVEN - a store in specific state
      const store = useUserSelectionStore()
      setup(store)

      // WHEN - accessing hasSelection getter
      const result = store.hasSelection

      // THEN - returns expected boolean value
      expect(result).toBe(expected)
    })
  })
})
