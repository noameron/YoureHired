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
    <!-- Animated Background -->
    <div
      class="background-animation"
      aria-hidden="true"
    >
      <!-- Keyboard icon -->
      <div class="floating-icon icon-1">
        <svg
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            d="M20 5H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm-9 3h2v2h-2V8zm0 3h2v2h-2v-2zM8 8h2v2H8V8zm0 3h2v2H8v-2zm-1 2H5v-2h2v2zm0-3H5V8h2v2zm9 7H8v-2h8v2zm0-4h-2v-2h2v2zm0-3h-2V8h2v2zm3 3h-2v-2h2v2zm0-3h-2V8h2v2z"
          />
        </svg>
      </div>
      <!-- Monitor icon -->
      <div class="floating-icon icon-2">
        <svg
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            d="M21 2H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h7l-2 3v1h8v-1l-2-3h7c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 12H3V4h18v10z"
          />
        </svg>
      </div>
      <!-- Code brackets icon -->
      <div class="floating-icon icon-3">
        <svg
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"
          />
        </svg>
      </div>
      <!-- Mouse icon -->
      <div class="floating-icon icon-4">
        <svg
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            d="M13 1.07V9h7c0-4.08-3.05-7.44-7-7.93zM4 15c0 4.42 3.58 8 8 8s8-3.58 8-8v-4H4v4zm7-13.93C7.05 1.56 4 4.92 4 9h7V1.07z"
          />
        </svg>
      </div>
      <!-- Terminal icon -->
      <div class="floating-icon icon-5">
        <svg
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zM7.5 17l-1.41-1.41L9.67 12 6.09 8.41 7.5 7l5 5-5 5zm6.5 0v-2h4v2h-4z"
          />
        </svg>
      </div>
      <!-- Database icon -->
      <div class="floating-icon icon-6">
        <svg
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <ellipse
            cx="12"
            cy="5.5"
            rx="8"
            ry="3.5"
          />
          <path
            d="M4 5.5v5c0 1.93 3.58 3.5 8 3.5s8-1.57 8-3.5v-5c0 1.93-3.58 3.5-8 3.5S4 7.43 4 5.5z"
          />
          <path
            d="M4 10.5v5c0 1.93 3.58 3.5 8 3.5s8-1.57 8-3.5v-5c0 1.93-3.58 3.5-8 3.5s-8-1.57-8-3.5z"
          />
        </svg>
      </div>
    </div>

    <div class="content-wrapper">
      <h1>Select Your Target Role</h1>

      <div
        v-if="isLoading"
        data-testid="loading"
        class="loading"
      >
        <div class="loading-spinner" />
        <span>Loading roles...</span>
      </div>

      <div
        v-else-if="isSuccess"
        data-testid="success-message"
        class="success-card"
      >
        <div class="success-icon">
          <svg
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
            />
          </svg>
        </div>
        <h2>Selection Saved!</h2>
        <div class="success-details">
          <p><strong>Company:</strong> {{ store.companyName }}</p>
          <p><strong>Role:</strong> {{ store.role }}</p>
          <p v-if="store.roleDescription">
            <strong>Description:</strong> {{ store.roleDescription }}
          </p>
        </div>
      </div>

      <form
        v-else
        class="selection-form"
        @submit.prevent="handleSubmit"
      >
        <!-- Company Name Card -->
        <div class="form-card">
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
          >
          <span
            v-if="errors.companyName"
            id="error-companyName"
            data-testid="error-companyName"
            class="error-message"
          >
            {{ errors.companyName }}
          </span>
        </div>

        <!-- Role Card -->
        <div class="form-card">
          <label for="role">Role</label>
          <div class="select-wrapper">
            <select
              id="role"
              v-model="role"
              name="role"
              :class="{ error: errors.role }"
              :aria-invalid="!!errors.role"
              :aria-describedby="errors.role ? 'error-role' : undefined"
            >
              <option
                value=""
                disabled
              >
                Select a role
              </option>
              <option
                v-for="r in roles"
                :key="r.id"
                :value="r.id"
              >
                {{ r.label }}
              </option>
            </select>
            <svg
              class="select-arrow"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M7 10l5 5 5-5z" />
            </svg>
          </div>
          <span
            v-if="errors.role"
            id="error-role"
            data-testid="error-role"
            class="error-message"
          >
            {{ errors.role }}
          </span>
        </div>

        <!-- Role Description Card -->
        <div class="form-card">
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
          />
          <span class="char-count">{{ roleDescription.length }} / {{ ROLE_DESCRIPTION_MAX }}</span>
          <span
            v-if="errors.roleDescription"
            id="error-roleDescription"
            data-testid="error-roleDescription"
            class="error-message"
          >
            {{ errors.roleDescription }}
          </span>
        </div>

        <div
          v-if="errors.submit"
          class="submit-error"
        >
          {{ errors.submit }}
        </div>

        <button
          type="submit"
          class="submit-button"
          :disabled="isSubmitting"
        >
          {{ isSubmitting ? 'Submitting...' : 'Start Practice' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
  /* Base layout */
  .role-selection {
    min-height: 100vh;
    background: #f0f2f5;
    position: relative;
    overflow: hidden;
  }

  .content-wrapper {
    max-width: 520px;
    margin: 0 auto;
    padding: 2.5rem 1.5rem;
    position: relative;
    z-index: 1;
  }

  h1 {
    margin-bottom: 2rem;
    color: #1a1a2e;
    font-size: 1.75rem;
    font-weight: 600;
    text-align: center;
  }

  /* Animated Background */
  .background-animation {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
  }

  .floating-icon {
    position: absolute;
    width: 48px;
    height: 48px;
    color: #0066ff;
    opacity: 0.12;
    animation: orbit 25s linear infinite;
  }

  .floating-icon svg {
    width: 100%;
    height: 100%;
  }

  .icon-1 {
    top: 15%;
    left: 20%;
    animation-duration: 22s;
    animation-delay: 0s;
  }

  .icon-2 {
    top: 25%;
    right: 15%;
    animation-duration: 28s;
    animation-delay: -4s;
  }

  .icon-3 {
    top: 50%;
    left: 10%;
    animation-duration: 20s;
    animation-delay: -8s;
  }

  .icon-4 {
    bottom: 30%;
    right: 20%;
    animation-duration: 26s;
    animation-delay: -12s;
  }

  .icon-5 {
    bottom: 15%;
    left: 25%;
    animation-duration: 24s;
    animation-delay: -16s;
  }

  .icon-6 {
    top: 60%;
    right: 10%;
    animation-duration: 30s;
    animation-delay: -6s;
    width: 40px;
    height: 40px;
  }

  @keyframes orbit {
    0% {
      transform: rotate(0deg) translateX(80px) rotate(0deg);
    }
    100% {
      transform: rotate(360deg) translateX(80px) rotate(-360deg);
    }
  }

  /* Respect reduced motion preference */
  @media (prefers-reduced-motion: reduce) {
    .floating-icon {
      animation: none;
    }
  }

  /* Loading state */
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    color: #6c757d;
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e0e0e0;
    border-top-color: #0066ff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* Success card */
  .success-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    text-align: center;
  }

  .success-icon {
    width: 64px;
    height: 64px;
    margin: 0 auto 1rem;
    color: #10b981;
  }

  .success-icon svg {
    width: 100%;
    height: 100%;
  }

  .success-card h2 {
    margin: 0 0 1.5rem;
    color: #1a1a2e;
    font-size: 1.5rem;
  }

  .success-details {
    text-align: left;
    background: #f8f9fa;
    border-radius: 12px;
    padding: 1.25rem;
  }

  .success-details p {
    margin: 0.5rem 0;
    color: #1a1a2e;
    font-size: 0.95rem;
  }

  .success-details p:first-child {
    margin-top: 0;
  }

  .success-details p:last-child {
    margin-bottom: 0;
  }

  .success-details strong {
    color: #6c757d;
    font-weight: 500;
  }

  /* Form cards */
  .selection-form {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .form-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    transition:
      box-shadow 0.2s ease,
      transform 0.2s ease;
  }

  .form-card:hover {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  }

  .form-card:focus-within {
    box-shadow: 0 4px 20px rgba(0, 102, 255, 0.15);
  }

  /* Labels */
  label {
    display: block;
    margin-bottom: 0.75rem;
    font-weight: 600;
    font-size: 0.95rem;
    color: #1a1a2e;
  }

  /* Input fields */
  input,
  select,
  textarea {
    width: 100%;
    padding: 0.875rem 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    font-size: 1rem;
    font-family: inherit;
    box-sizing: border-box;
    background: #ffffff;
    color: #1a1a2e;
    transition:
      border-color 0.2s ease,
      box-shadow 0.2s ease;
  }

  input::placeholder,
  textarea::placeholder {
    color: #9ca3af;
  }

  input:focus,
  select:focus,
  textarea:focus {
    outline: none;
    border-color: #0066ff;
    box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.12);
  }

  input.error,
  select.error,
  textarea.error {
    border-color: #dc3545;
  }

  input.error:focus,
  select.error:focus,
  textarea.error:focus {
    box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.12);
  }

  /* Select wrapper for custom arrow */
  .select-wrapper {
    position: relative;
  }

  .select-wrapper select {
    appearance: none;
    padding-right: 2.5rem;
    cursor: pointer;
  }

  .select-arrow {
    position: absolute;
    right: 0.875rem;
    top: 50%;
    transform: translateY(-50%);
    width: 20px;
    height: 20px;
    color: #6c757d;
    pointer-events: none;
  }

  /* Textarea */
  textarea {
    resize: vertical;
    min-height: 100px;
  }

  /* Character count */
  .char-count {
    display: block;
    text-align: right;
    font-size: 0.8rem;
    color: #9ca3af;
    margin-top: 0.5rem;
  }

  /* Error messages */
  .error-message {
    display: block;
    color: #dc3545;
    font-size: 0.875rem;
    margin-top: 0.5rem;
    font-weight: 500;
  }

  .submit-error {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #dc2626;
    font-size: 0.95rem;
  }

  /* Submit button */
  .submit-button {
    width: 100%;
    padding: 1rem 1.5rem;
    background: #0066ff;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition:
      background 0.2s ease,
      transform 0.1s ease,
      box-shadow 0.2s ease;
    box-shadow: 0 2px 8px rgba(0, 102, 255, 0.3);
  }

  .submit-button:hover:not(:disabled) {
    background: #0052cc;
    box-shadow: 0 4px 12px rgba(0, 102, 255, 0.4);
  }

  .submit-button:active:not(:disabled) {
    transform: translateY(1px);
  }

  .submit-button:disabled {
    background: #9ca3af;
    cursor: not-allowed;
    box-shadow: none;
  }

  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .content-wrapper {
      padding: 1.5rem 1rem;
    }

    h1 {
      font-size: 1.5rem;
    }

    .form-card {
      padding: 1.25rem;
    }

    .floating-icon {
      width: 36px;
      height: 36px;
    }

    .icon-6 {
      width: 30px;
      height: 30px;
    }
  }
</style>
