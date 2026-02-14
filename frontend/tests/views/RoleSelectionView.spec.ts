import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import type { ComponentPublicInstance } from 'vue'
import { setActivePinia, createPinia } from 'pinia'
import RoleSelectionView from '@/views/RoleSelectionView.vue'
import { useUserSelectionStore } from '@/stores/userSelection'
import * as api from '@/services/api'
import type { RolesResponse, UserSelectionResponse, UserSelectionError } from '@/types/api'

type TestWrapper = VueWrapper<ComponentPublicInstance>

// Mock the API module
vi.mock('@/services/api')

// Mock vue-router
const mockPush = vi.fn()
let mockRouteQuery: Record<string, string> = {}
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  }),
  useRoute: () => ({
    query: mockRouteQuery
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
    mockRouteQuery = {}
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

    it('stores roleId in addition to role label on successful submission', async () => {
      // GIVEN - the component is mounted with valid form data
      const store = useUserSelectionStore()
      const wrapper = await mountComponent()
      await fillFormData(wrapper, { companyName: 'Test Corp', role: 'backend_developer' })

      // WHEN - form is submitted successfully
      await submitForm(wrapper)

      // THEN - store contains both roleId and role label
      expect(store.roleId).toBe('backend_developer')
      expect(store.role).toBe('Backend Developer')
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

  describe('form pre-fill from query params', () => {
    it('pre-fills all fields from query params', async () => {
      // GIVEN - query params contain all form values
      mockRouteQuery = {
        company: 'Acme Corp',
        role: 'frontend_developer',
        description: 'Build React apps with TypeScript and modern tooling'
      }

      // WHEN - component mounts
      const wrapper = await mountComponent()

      // THEN - form fields are populated from query params
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

    it('shows empty fields when no query params', async () => {
      // GIVEN - no query params (empty object)
      mockRouteQuery = {}

      // WHEN - component mounts
      const wrapper = await mountComponent()

      // THEN - form fields are empty
      expect((wrapper.find('input[name="companyName"]').element as HTMLInputElement).value).toBe('')
      expect((wrapper.find('select[name="role"]').element as HTMLSelectElement).value).toBe('')
      expect(
        (wrapper.find('textarea[name="roleDescription"]').element as HTMLTextAreaElement).value
      ).toBe('')
    })

    it('pre-fills partial query params', async () => {
      // GIVEN - query params contain only company name
      mockRouteQuery = {
        company: 'Partial Corp'
      }

      // WHEN - component mounts
      const wrapper = await mountComponent()

      // THEN - only company field is populated, others are empty
      expect((wrapper.find('input[name="companyName"]').element as HTMLInputElement).value).toBe(
        'Partial Corp'
      )
      expect((wrapper.find('select[name="role"]').element as HTMLSelectElement).value).toBe('')
      expect(
        (wrapper.find('textarea[name="roleDescription"]').element as HTMLTextAreaElement).value
      ).toBe('')
    })

    it('query params override store values', async () => {
      // GIVEN - store has values
      const store = useUserSelectionStore()
      store.setSelection({
        companyName: 'Store Corp',
        role: 'fullstack_developer',
        roleDescription: 'Store description',
        sessionId: 'session-xyz',
        roleId: 'fullstack_developer'
      })

      // AND - query params have different values
      mockRouteQuery = {
        company: 'Query Corp',
        role: 'backend_developer'
      }

      // WHEN - component mounts
      const wrapper = await mountComponent()

      // THEN - form shows query param values, not store values
      expect((wrapper.find('input[name="companyName"]').element as HTMLInputElement).value).toBe(
        'Query Corp'
      )
      expect((wrapper.find('select[name="role"]').element as HTMLSelectElement).value).toBe(
        'backend_developer'
      )
      // Description is empty because it's not in query params
      expect(
        (wrapper.find('textarea[name="roleDescription"]').element as HTMLTextAreaElement).value
      ).toBe('')
    })

    it('pre-fills role select with role ID from query params after cancel', async () => {
      // GIVEN - user returns from cancel with role ID in query params
      mockRouteQuery = {
        company: 'Acme Corp',
        role: 'frontend_developer',
        description: 'Build React apps'
      }

      // WHEN - component mounts and roles load
      const wrapper = await mountComponent()

      // THEN - role select is pre-filled with the role ID value
      expect((wrapper.find('select[name="role"]').element as HTMLSelectElement).value).toBe(
        'frontend_developer'
      )
    })
  })

  describe('reactive error clearing', () => {
    it('clears company name error when user types in company name field', async () => {
      // GIVEN - the component is mounted
      const wrapper = await mountComponent()

      // WHEN - form is submitted with empty company name to trigger error
      await fillFormData(wrapper, { role: 'backend_developer' })
      await submitForm(wrapper)

      // THEN - company name error is displayed
      expect(wrapper.find('[data-testid="error-companyName"]').exists()).toBe(true)

      // WHEN - user types in company name field
      await fillFormData(wrapper, { companyName: 'Test Corp' })

      // THEN - company name error is cleared
      expect(wrapper.find('[data-testid="error-companyName"]').exists()).toBe(false)
    })

    it('clears role error when user selects a role', async () => {
      // GIVEN - the component is mounted
      const wrapper = await mountComponent()

      // WHEN - form is submitted with no role selected to trigger error
      await fillFormData(wrapper, { companyName: 'Test Corp' })
      await submitForm(wrapper)

      // THEN - role error is displayed
      expect(wrapper.find('[data-testid="error-role"]').exists()).toBe(true)

      // WHEN - user selects a role
      await fillFormData(wrapper, { role: 'backend_developer' })

      // THEN - role error is cleared
      expect(wrapper.find('[data-testid="error-role"]').exists()).toBe(false)
    })

    it('clears role description error when user types in description field', async () => {
      // GIVEN - the component is mounted
      const wrapper = await mountComponent()

      // WHEN - form is submitted with too-long description to trigger error
      await fillFormData(wrapper, {
        companyName: 'Test Corp',
        role: 'backend_developer',
        roleDescription: 'A'.repeat(8001)
      })
      await submitForm(wrapper)

      // THEN - role description error is displayed
      expect(wrapper.find('[data-testid="error-roleDescription"]').exists()).toBe(true)

      // WHEN - user changes the description to a valid value
      await fillFormData(wrapper, {
        roleDescription: 'A valid role description.'
      })

      // THEN - role description error is cleared
      expect(wrapper.find('[data-testid="error-roleDescription"]').exists()).toBe(false)
    })

    it('clears submit error when any field changes', async () => {
      // GIVEN - the component is mounted and API will return an error
      const mockErrorResponse: UserSelectionError = {
        success: false,
        error: {
          code: 'SERVER_ERROR',
          message: 'Server error occurred',
          details: {}
        }
      }
      vi.mocked(api.submitUserSelection).mockResolvedValue(mockErrorResponse)

      const wrapper = await mountComponent()

      // WHEN - form is submitted to get a submit error
      await fillFormData(wrapper, { companyName: 'Test Corp', role: 'backend_developer' })
      await submitForm(wrapper)

      // THEN - submit error is displayed
      expect(wrapper.find('.submit-error').exists()).toBe(true)

      // WHEN - user changes company name value
      await fillFormData(wrapper, { companyName: 'New Corp' })

      // THEN - submit error is cleared
      expect(wrapper.find('.submit-error').exists()).toBe(false)
    })

    it('does not clear other field errors when only one field changes', async () => {
      // GIVEN - the component is mounted
      const wrapper = await mountComponent()

      // WHEN - form is submitted with BOTH company name empty AND role empty
      await submitForm(wrapper)

      // THEN - both errors are displayed
      expect(wrapper.find('[data-testid="error-companyName"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="error-role"]').exists()).toBe(true)

      // WHEN - user types in company name
      await fillFormData(wrapper, { companyName: 'Test Corp' })

      // THEN - company name error is cleared but role error remains
      expect(wrapper.find('[data-testid="error-companyName"]').exists()).toBe(false)
      expect(wrapper.find('[data-testid="error-role"]').exists()).toBe(true)
    })
  })
})
