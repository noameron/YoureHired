<script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { fetchRoles, submitUserSelection } from '@/services/api'
  import { useUserSelectionStore } from '@/stores/userSelection'
  import type { Role, UserSelectionError } from '@/types/api'

  const store = useUserSelectionStore()

  // Form state
  const companyName = ref('')
  const role = ref('')
  const roleDescription = ref('')

  // UI state
  const roles = ref<Role[]>([])
  const isLoading = ref(true)
  const isSubmitting = ref(false)
  const isSuccess = ref(false)

  // Validation errors
  const errors = ref<{
    companyName?: string
    role?: string
    roleDescription?: string
    submit?: string
  }>({})

  // Validation constants (matching backend)
  const COMPANY_NAME_MIN = 2
  const COMPANY_NAME_MAX = 100
  const ROLE_DESCRIPTION_MIN = 30
  const ROLE_DESCRIPTION_MAX = 8000

  onMounted(async () => {
    try {
      const response = await fetchRoles()
      roles.value = response.roles
    } catch (error) {
      console.error('Failed to fetch roles:', error)
    } finally {
      isLoading.value = false
    }
  })

  function validate(): boolean {
    errors.value = {}

    // Company name validation
    const trimmedCompanyName = companyName.value.trim()
    if (!trimmedCompanyName) {
      errors.value.companyName = 'Company name is required'
    } else if (trimmedCompanyName.length < COMPANY_NAME_MIN) {
      errors.value.companyName = `Company name must be at least ${COMPANY_NAME_MIN} characters`
    } else if (trimmedCompanyName.length > COMPANY_NAME_MAX) {
      errors.value.companyName = `Company name must be at most ${COMPANY_NAME_MAX} characters`
    }

    // Role validation
    if (!role.value) {
      errors.value.role = 'Please select a role'
    }

    // Role description validation (optional, but if provided must meet length requirements)
    const trimmedDescription = roleDescription.value.trim()
    if (trimmedDescription && trimmedDescription.length < ROLE_DESCRIPTION_MIN) {
      errors.value.roleDescription = `Role description must be at least ${ROLE_DESCRIPTION_MIN} characters`
    } else if (trimmedDescription.length > ROLE_DESCRIPTION_MAX) {
      errors.value.roleDescription = `Role description must be at most ${ROLE_DESCRIPTION_MAX} characters`
    }

    return Object.keys(errors.value).length === 0
  }

  async function handleSubmit() {
    if (!validate()) {
      return
    }

    isSubmitting.value = true
    errors.value = {}

    try {
      const trimmedDescription = roleDescription.value.trim()
      const result = await submitUserSelection({
        company_name: companyName.value.trim(),
        role: role.value,
        role_description: trimmedDescription || undefined
      })

      if (result.success) {
        // Update store with selection data
        store.setSelection({
          companyName: result.data.company_name,
          role: result.data.role,
          roleDescription: result.data.role_description,
          sessionId: result.data.session_id
        })
        isSuccess.value = true
      } else {
        // Handle validation error from API
        const errorResult = result as UserSelectionError
        errors.value.submit = errorResult.error.message
      }
    } catch (error) {
      console.error('Failed to submit selection:', error)
      errors.value.submit = 'An unexpected error occurred. Please try again.'
    } finally {
      isSubmitting.value = false
    }
  }
</script>

<template>
  <div class="role-selection">
    <h1>Select Your Target Role</h1>

    <div v-if="isLoading" data-testid="loading" class="loading">Loading roles...</div>

    <div v-else-if="isSuccess" data-testid="success-message" class="success">
      <h2>Selection Saved!</h2>
      <p>Company: {{ store.companyName }}</p>
      <p>Role: {{ store.role }}</p>
      <p v-if="store.roleDescription">Description: {{ store.roleDescription }}</p>
    </div>

    <form v-else @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="companyName">Company Name</label>
        <input
          id="companyName"
          v-model="companyName"
          type="text"
          name="companyName"
          placeholder="Enter company name"
          :maxlength="COMPANY_NAME_MAX"
          :class="{ error: errors.companyName }"
          :aria-invalid="!!errors.companyName"
          :aria-describedby="errors.companyName ? 'error-companyName' : undefined"
        />
        <span
          v-if="errors.companyName"
          id="error-companyName"
          data-testid="error-companyName"
          class="error-message"
        >
          {{ errors.companyName }}
        </span>
      </div>

      <div class="form-group">
        <label for="role">Role</label>
        <select
          id="role"
          v-model="role"
          name="role"
          :class="{ error: errors.role }"
          :aria-invalid="!!errors.role"
          :aria-describedby="errors.role ? 'error-role' : undefined"
        >
          <option value="" disabled>Select a role</option>
          <option v-for="r in roles" :key="r.id" :value="r.id">
            {{ r.label }}
          </option>
        </select>
        <span v-if="errors.role" id="error-role" data-testid="error-role" class="error-message">
          {{ errors.role }}
        </span>
      </div>

      <div class="form-group">
        <label for="roleDescription">Role Description (Optional)</label>
        <textarea
          id="roleDescription"
          v-model="roleDescription"
          name="roleDescription"
          placeholder="Describe your target role or specific areas you want to practice..."
          rows="4"
          :maxlength="ROLE_DESCRIPTION_MAX"
          :class="{ error: errors.roleDescription }"
          :aria-invalid="!!errors.roleDescription"
          :aria-describedby="errors.roleDescription ? 'error-roleDescription' : undefined"
        ></textarea>
        <span class="char-count"> {{ roleDescription.length }} / {{ ROLE_DESCRIPTION_MAX }} </span>
        <span
          v-if="errors.roleDescription"
          id="error-roleDescription"
          data-testid="error-roleDescription"
          class="error-message"
        >
          {{ errors.roleDescription }}
        </span>
      </div>

      <div v-if="errors.submit" class="submit-error">
        {{ errors.submit }}
      </div>

      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Submitting...' : 'Start Practice' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
  .role-selection {
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem;
  }

  h1 {
    margin-bottom: 2rem;
    color: #333;
  }

  .loading {
    text-align: center;
    padding: 2rem;
    color: #666;
  }

  .success {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 4px;
    padding: 2rem;
    color: #155724;
  }

  .success h2 {
    margin-top: 0;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #333;
  }

  input,
  select,
  textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
    box-sizing: border-box;
  }

  input:focus,
  select:focus,
  textarea:focus {
    outline: none;
    border-color: #4a90d9;
    box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.2);
  }

  input.error,
  select.error,
  textarea.error {
    border-color: #dc3545;
  }

  .error-message {
    display: block;
    color: #dc3545;
    font-size: 0.875rem;
    margin-top: 0.25rem;
  }

  .char-count {
    display: block;
    text-align: right;
    font-size: 0.75rem;
    color: #666;
    margin-top: 0.25rem;
  }

  .submit-error {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    padding: 0.75rem;
    color: #721c24;
    margin-bottom: 1rem;
  }

  button[type='submit'] {
    width: 100%;
    padding: 1rem;
    background: #4a90d9;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  }

  button[type='submit']:hover:not(:disabled) {
    background: #3a7bc8;
  }

  button[type='submit']:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
</style>
