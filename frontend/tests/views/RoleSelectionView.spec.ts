import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import type { ComponentPublicInstance } from 'vue'
import { setActivePinia, createPinia } from 'pinia'
import RoleSelectionView from '@/views/RoleSelectionView.vue'
import { useUserSelectionStore } from '@/stores/userSelection'
import * as api from '@/services/api'
import type { RolesResponse, UserSelectionResponse } from '@/types/api'

type TestWrapper = VueWrapper<ComponentPublicInstance>

// Mock the API module
vi.mock('@/services/api')

// Mock vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

// Test data
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

// Helper to mount component with default setup
async function mountComponent(): Promise<VueWrapper> {
  const wrapper = mount(RoleSelectionView)
  await flushPromises()
  return wrapper
}

// Helper to fill form with data
async function fillFormData(
  wrapper: VueWrapper,
  data: { companyName?: string; role?: string; roleDescription?: string }
) {
  if (data.companyName !== undefined) {
    await wrapper.find('input[name="companyName"]').setValue(data.companyName)
  }
  if (data.role !== undefined) {
    await wrapper.find('select[name="role"]').setValue(data.role)
  }
  if (data.roleDescription !== undefined) {
    await wrapper.find('textarea[name="roleDescription"]').setValue(data.roleDescription)
  }
}

// Helper to submit form
async function submitForm(wrapper: VueWrapper) {
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

describe('RoleSelectionView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockPush.mockClear()
    vi.mocked(api.fetchRoles).mockResolvedValue(mockRoles)
    vi.mocked(api.submitUserSelection).mockResolvedValue(mockSuccessResponse)
  })

  describe('rendering', () => {
    it.each([
      { selector: 'form', description: 'form element' },
      { selector: 'input[name="companyName"]', description: 'company name input' },
      { selector: 'select[name="role"]', description: 'role dropdown' },
      { selector: 'textarea[name="roleDescription"]', description: 'role description textarea' },
      { selector: 'button[type="submit"]', description: 'submit button' }
    ])('renders $description', async ({ selector }) => {
      // GIVEN - the component is mounted
      const wrapper = await mountComponent()

      // THEN - the expected element exists
      expect(wrapper.find(selector).exists()).toBe(true)
    })
  })

  describe('roles loading', () => {
    it('fetches roles on mount', async () => {
      // GIVEN - the component is being mounted
      await mountComponent()

      // THEN - fetchRoles is called once
      expect(api.fetchRoles).toHaveBeenCalledOnce()
    })

    it('populates dropdown with fetched roles', async () => {
      // GIVEN - the component is mounted and roles are fetched
      const wrapper = await mountComponent()

      // WHEN - accessing the role dropdown options
      const options = wrapper.findAll('select[name="role"] option')

      // THEN - all roles are present (placeholder + 3 roles)
      expect(options.length).toBe(4)
      expect(options[1].text()).toBe('Frontend Developer')
      expect(options[2].text()).toBe('Backend Developer')
      expect(options[3].text()).toBe('Full Stack Developer')
    })

    it('shows loading state while fetching roles', async () => {
      // GIVEN - a delayed promise for role fetching
      let resolvePromise: (value: RolesResponse) => void
      vi.mocked(api.fetchRoles).mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve
        })
      )

      // WHEN - component mounts with delayed roles
      const wrapper = mount(RoleSelectionView)

      // THEN - loading indicator is shown
      expect(wrapper.find('[data-testid="loading"]').exists()).toBe(true)

      // WHEN - promise resolves
      resolvePromise!(mockRoles)
      await flushPromises()

      // THEN - loading indicator is hidden
      expect(wrapper.find('[data-testid="loading"]').exists()).toBe(false)
    })

    it('handles role fetch failure gracefully', async () => {
      // GIVEN - fetchRoles will fail
      vi.mocked(api.fetchRoles).mockRejectedValue(new Error('Network error'))

      // WHEN - component mounts
      const wrapper = await mountComponent()

      // THEN - form renders with empty roles dropdown
      expect(wrapper.find('[data-testid="loading"]').exists()).toBe(false)
      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('select[name="role"]').exists()).toBe(true)

      const options = wrapper.findAll('select[name="role"] option')
      expect(options.length).toBe(1) // Just the placeholder
    })
  })

  describe('form validation', () => {
    it.each([
      {
        description: 'missing company name',
        setup: async (wrapper: TestWrapper) => {
          await wrapper.find('select[name="role"]').setValue('backend_developer')
        },
        errorTestId: 'error-companyName'
      },
      {
        description: 'missing role',
        setup: async (wrapper: TestWrapper) => {
          await wrapper.find('input[name="companyName"]').setValue('Test Corp')
        },
        errorTestId: 'error-role'
      },
      {
        description: 'company name too short',
        setup: async (wrapper: TestWrapper) => {
          await wrapper.find('input[name="companyName"]').setValue('A')
          await wrapper.find('select[name="role"]').setValue('backend_developer')
        },
        errorTestId: 'error-companyName'
      },
      {
        description: 'company name too long',
        setup: async (wrapper: TestWrapper) => {
          await wrapper.find('input[name="companyName"]').setValue('A'.repeat(101))
          await wrapper.find('select[name="role"]').setValue('backend_developer')
        },
        errorTestId: 'error-companyName'
      },
      {
        description: 'role description too short',
        setup: async (wrapper: TestWrapper) => {
          await wrapper.find('input[name="companyName"]').setValue('Test Corp')
          await wrapper.find('select[name="role"]').setValue('backend_developer')
          await wrapper.find('textarea[name="roleDescription"]').setValue('Short')
        },
        errorTestId: 'error-roleDescription'
      }
    ])('shows error when $description', async ({ setup, errorTestId }) => {
      // GIVEN - the component is mounted
      const wrapper = mount(RoleSelectionView)
      await flushPromises()

      // WHEN - submitting form with invalid data
      await setup(wrapper)
      await wrapper.find('form').trigger('submit')

      // THEN - appropriate error message is displayed
      expect(wrapper.find(`[data-testid="${errorTestId}"]`).exists()).toBe(true)
    })
  })

  describe('form submission', () => {
    it.each([
      {
        description: 'without role description',
        roleDescription: undefined,
        expectedPayload: {
          company_name: 'Test Corp',
          role: 'backend_developer',
          role_description: undefined
        }
      },
      {
        description: 'with role description',
        roleDescription:
          'This is a detailed description for the role that exceeds the minimum character requirement.',
        expectedPayload: {
          company_name: 'Test Corp',
          role: 'backend_developer',
          role_description:
            'This is a detailed description for the role that exceeds the minimum character requirement.'
        }
      }
    ])('calls submitUserSelection $description', async ({ roleDescription, expectedPayload }) => {
      // GIVEN - the component is mounted with valid form data
      const wrapper = await mountComponent()

      await fillFormData(wrapper, {
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription
      })

      // WHEN - submitting the form
      await submitForm(wrapper)

      // THEN - API is called with correct payload
      expect(api.submitUserSelection).toHaveBeenCalledWith(expectedPayload)
    })

    it('shows success message on successful submission', async () => {
      // GIVEN - the component is mounted with valid form data
      const wrapper = await mountComponent()
      await fillFormData(wrapper, { companyName: 'Test Corp', role: 'backend_developer' })

      // WHEN - form is submitted successfully
      await submitForm(wrapper)

      // THEN - success message is displayed
      expect(wrapper.find('[data-testid="success-message"]').exists()).toBe(true)
    })

    it('navigates to /practice on successful submission', async () => {
      // GIVEN - the component is mounted with valid form data
      const wrapper = await mountComponent()
      await fillFormData(wrapper, { companyName: 'Test Corp', role: 'backend_developer' })

      // WHEN - form is submitted successfully
      await submitForm(wrapper)

      // THEN - router navigates to /practice
      expect(mockPush).toHaveBeenCalledWith('/practice')
    })

    it('disables submit button while submitting', async () => {
      // GIVEN - a delayed submission promise
      let resolvePromise: (value: UserSelectionResponse) => void
      vi.mocked(api.submitUserSelection).mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve
        })
      )

      const wrapper = await mountComponent()
      await fillFormData(wrapper, { companyName: 'Test Corp', role: 'backend_developer' })

      // WHEN - form is submitted
      await wrapper.find('form').trigger('submit')

      // THEN - submit button is disabled
      expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()

      // WHEN - promise resolves
      resolvePromise!(mockSuccessResponse)
      await flushPromises()

      // THEN - submission completes (button re-enabled or form replaced)
    })
  })

  describe('form pre-fill from store', () => {
    it('pre-fills form fields when store has values', async () => {
      // GIVEN - store has selection values
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Acme Corp',
        role: 'frontend_developer',
        roleDescription: 'Build React apps with TypeScript and modern tooling',
        sessionId: 'session-abc'
      })

      // WHEN - component mounts
      const wrapper = await mountComponent()

      // THEN - form fields are populated
      expect((wrapper.find('input[name="companyName"]').element as HTMLInputElement).value).toBe(
        'Acme Corp'
      )
      expect((wrapper.find('select[name="role"]').element as HTMLSelectElement).value).toBe(
        'frontend_developer'
      )
      expect(
        (wrapper.find('textarea[name="roleDescription"]').element as HTMLTextAreaElement).value
      ).toBe('Build React apps with TypeScript and modern tooling')
    })

    it('shows empty fields when store values are empty', async () => {
      // GIVEN - store has empty values (default state)
      const store = useUserSelectionStore()
      expect(store.companyName).toBe('')
      expect(store.role).toBe('')
      expect(store.roleDescription).toBeNull()

      // WHEN - component mounts
      const wrapper = await mountComponent()

      // THEN - form fields are empty
      expect((wrapper.find('input[name="companyName"]').element as HTMLInputElement).value).toBe('')
      expect((wrapper.find('select[name="role"]').element as HTMLSelectElement).value).toBe('')
      expect(
        (wrapper.find('textarea[name="roleDescription"]').element as HTMLTextAreaElement).value
      ).toBe('')
    })

    it('shows empty textarea when roleDescription is null in store', async () => {
      // GIVEN - store has null roleDescription
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: null,
        sessionId: 'session-xyz'
      })

      // WHEN - component mounts
      const wrapper = await mountComponent()

      // THEN - textarea shows empty string
      expect(
        (wrapper.find('textarea[name="roleDescription"]').element as HTMLTextAreaElement).value
      ).toBe('')
    })

    it('pre-fills only some fields when store has partial values', async () => {
      // GIVEN - store has only company name and role
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Partial Corp',
        role: 'fullstack_developer',
        roleDescription: null,
        sessionId: null
      })

      // WHEN - component mounts
      const wrapper = await mountComponent()

      // THEN - only populated fields are pre-filled
      expect((wrapper.find('input[name="companyName"]').element as HTMLInputElement).value).toBe(
        'Partial Corp'
      )
      expect((wrapper.find('select[name="role"]').element as HTMLSelectElement).value).toBe(
        'fullstack_developer'
      )
      expect(
        (wrapper.find('textarea[name="roleDescription"]').element as HTMLTextAreaElement).value
      ).toBe('')
    })
  })
})
