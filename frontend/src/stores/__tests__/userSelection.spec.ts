import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserSelectionStore } from '../userSelection'

describe('userSelection store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('initial state', () => {
    it('has empty companyName', () => {
      const store = useUserSelectionStore()
      expect(store.companyName).toBe('')
    })

    it('has empty role', () => {
      const store = useUserSelectionStore()
      expect(store.role).toBe('')
    })

    it('has null roleDescription', () => {
      const store = useUserSelectionStore()
      expect(store.roleDescription).toBeNull()
    })

    it('has null sessionId', () => {
      const store = useUserSelectionStore()
      expect(store.sessionId).toBeNull()
    })
  })

  describe('setSelection action', () => {
    it('sets companyName', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: null,
        sessionId: 'abc-123'
      })
      expect(store.companyName).toBe('Test Corp')
    })

    it('sets role', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'frontend_developer',
        roleDescription: null,
        sessionId: 'abc-123'
      })
      expect(store.role).toBe('frontend_developer')
    })

    it('sets roleDescription when provided', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: 'Senior position focusing on APIs',
        sessionId: 'abc-123'
      })
      expect(store.roleDescription).toBe('Senior position focusing on APIs')
    })

    it('sets roleDescription to null when not provided', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: null,
        sessionId: 'abc-123'
      })
      expect(store.roleDescription).toBeNull()
    })

    it('sets sessionId', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: null,
        sessionId: 'session-uuid-12345'
      })
      expect(store.sessionId).toBe('session-uuid-12345')
    })
  })

  describe('clearSelection action', () => {
    it('resets companyName to empty', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: 'Description',
        sessionId: 'abc-123'
      })
      store.clearSelection()
      expect(store.companyName).toBe('')
    })

    it('resets role to empty', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: 'Description',
        sessionId: 'abc-123'
      })
      store.clearSelection()
      expect(store.role).toBe('')
    })

    it('resets roleDescription to null', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: 'Description',
        sessionId: 'abc-123'
      })
      store.clearSelection()
      expect(store.roleDescription).toBeNull()
    })

    it('resets sessionId to null', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: 'Description',
        sessionId: 'abc-123'
      })
      store.clearSelection()
      expect(store.sessionId).toBeNull()
    })
  })

  describe('hasSelection getter', () => {
    it('returns false when no selection made', () => {
      const store = useUserSelectionStore()
      expect(store.hasSelection).toBe(false)
    })

    it('returns true when selection is set', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: null,
        sessionId: 'abc-123'
      })
      expect(store.hasSelection).toBe(true)
    })

    it('returns false after clearSelection', () => {
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: null,
        sessionId: 'abc-123'
      })
      store.clearSelection()
      expect(store.hasSelection).toBe(false)
    })
  })
})
