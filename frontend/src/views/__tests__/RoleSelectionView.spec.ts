import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import RoleSelectionView from '../RoleSelectionView.vue'
import * as api from '@/services/api'
import type { RolesResponse, UserSelectionResponse } from '@/types/api'

// Mock the API module
vi.mock('@/services/api')

const mockRoles: RolesResponse = {
  roles: [
    { id: 'frontend_developer', label: 'Frontend Developer' },
    { id: 'backend_developer', label: 'Backend Developer' },
    { id: 'fullstack_developer', label: 'Full Stack Developer' }
  ]
}

const mockSuccessResponse: UserSelectionResponse = {
  success: true,
  data: {
    company_name: 'Test Corp',
    role: 'Backend Developer',
    role_description: null,
    session_id: 'test-session-123'
  },
  next_step: '/api/generate-tasks'
}

describe('RoleSelectionView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.mocked(api.fetchRoles).mockResolvedValue(mockRoles)
    vi.mocked(api.submitUserSelection).mockResolvedValue(mockSuccessResponse)
  })

  describe('rendering', () => {
    it('renders the form', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      expect(wrapper.find('form').exists()).toBe(true)
    })

    it('renders company name input', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      expect(wrapper.find('input[name="companyName"]').exists()).toBe(true)
    })

    it('renders role dropdown', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      expect(wrapper.find('select[name="role"]').exists()).toBe(true)
    })

    it('renders role description textarea', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      expect(wrapper.find('textarea[name="roleDescription"]').exists()).toBe(true)
    })

    it('renders submit button', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
    })
  })

  describe('roles loading', () => {
    it('fetches roles on mount', async () => {
      mount(RoleSelectionView)
      await flushPromises()

      expect(api.fetchRoles).toHaveBeenCalledOnce()
    })

    it('populates dropdown with fetched roles', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      const options = wrapper.findAll('select[name="role"] option')
      // First option is placeholder, then 3 roles
      expect(options.length).toBe(4)
      expect(options[1].text()).toBe('Frontend Developer')
      expect(options[2].text()).toBe('Backend Developer')
      expect(options[3].text()).toBe('Full Stack Developer')
    })

    it('shows loading state while fetching roles', async () => {
      // Delay the promise resolution
      let resolvePromise: (value: RolesResponse) => void
      vi.mocked(api.fetchRoles).mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve
        })
      )

      const wrapper = mount(RoleSelectionView)

      // Should show loading indicator
      expect(wrapper.find('[data-testid="loading"]').exists()).toBe(true)

      // Resolve the promise
      resolvePromise!(mockRoles)
      await flushPromises()

      // Loading should be gone
      expect(wrapper.find('[data-testid="loading"]').exists()).toBe(false)
    })

    it('handles role fetch failure gracefully', async () => {
      vi.mocked(api.fetchRoles).mockRejectedValue(new Error('Network error'))

      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      // Loading should be gone
      expect(wrapper.find('[data-testid="loading"]').exists()).toBe(false)

      // Form should still render with empty roles dropdown
      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('select[name="role"]').exists()).toBe(true)

      // Only the placeholder option should be present
      const options = wrapper.findAll('select[name="role"] option')
      expect(options.length).toBe(1) // Just the "Select a role" placeholder
    })
  })

  describe('form validation', () => {
    it('shows error when submitting without company name', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      // Select a role but leave company name empty
      await wrapper.find('select[name="role"]').setValue('backend_developer')
      await wrapper.find('form').trigger('submit')

      expect(wrapper.find('[data-testid="error-companyName"]').exists()).toBe(true)
    })

    it('shows error when submitting without role', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      // Fill company name but leave role empty
      await wrapper.find('input[name="companyName"]').setValue('Test Corp')
      await wrapper.find('form').trigger('submit')

      expect(wrapper.find('[data-testid="error-role"]').exists()).toBe(true)
    })

    it('shows error when company name is too short', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      await wrapper.find('input[name="companyName"]').setValue('A')
      await wrapper.find('select[name="role"]').setValue('backend_developer')
      await wrapper.find('form').trigger('submit')

      expect(wrapper.find('[data-testid="error-companyName"]').exists()).toBe(true)
    })

    it('shows error when company name is too long', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      await wrapper.find('input[name="companyName"]').setValue('A'.repeat(101))
      await wrapper.find('select[name="role"]').setValue('backend_developer')
      await wrapper.find('form').trigger('submit')

      expect(wrapper.find('[data-testid="error-companyName"]').exists()).toBe(true)
    })

    it('shows error when role description is too short', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      await wrapper.find('input[name="companyName"]').setValue('Test Corp')
      await wrapper.find('select[name="role"]').setValue('backend_developer')
      await wrapper.find('textarea[name="roleDescription"]').setValue('Short')
      await wrapper.find('form').trigger('submit')

      expect(wrapper.find('[data-testid="error-roleDescription"]').exists()).toBe(true)
    })
  })

  describe('form submission', () => {
    it('calls submitUserSelection with correct data', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      await wrapper.find('input[name="companyName"]').setValue('Test Corp')
      await wrapper.find('select[name="role"]').setValue('backend_developer')
      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(api.submitUserSelection).toHaveBeenCalledWith({
        company_name: 'Test Corp',
        role: 'backend_developer',
        role_description: undefined
      })
    })

    it('includes role description when provided', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      const description =
        'This is a detailed description for the role that exceeds the minimum character requirement.'
      await wrapper.find('input[name="companyName"]').setValue('Test Corp')
      await wrapper.find('select[name="role"]').setValue('backend_developer')
      await wrapper.find('textarea[name="roleDescription"]').setValue(description)
      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(api.submitUserSelection).toHaveBeenCalledWith({
        company_name: 'Test Corp',
        role: 'backend_developer',
        role_description: description
      })
    })

    it('shows success message on successful submission', async () => {
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      await wrapper.find('input[name="companyName"]').setValue('Test Corp')
      await wrapper.find('select[name="role"]').setValue('backend_developer')
      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(wrapper.find('[data-testid="success-message"]').exists()).toBe(true)
    })

    it('disables submit button while submitting', async () => {
      let resolvePromise: (value: UserSelectionResponse) => void
      vi.mocked(api.submitUserSelection).mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve
        })
      )

      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      await wrapper.find('input[name="companyName"]').setValue('Test Corp')
      await wrapper.find('select[name="role"]').setValue('backend_developer')
      await wrapper.find('form').trigger('submit')

      // Button should be disabled
      expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()

      // Resolve the promise
      resolvePromise!(mockSuccessResponse)
      await flushPromises()

      // Button should be enabled again (or form hidden)
      // Note: After success, the form may be replaced with success message
    })
  })
})
