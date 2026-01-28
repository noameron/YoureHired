<script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { fetchRoles, submitUserSelection } from '@/services/api'
  import { useUserSelectionStore } from '@/stores/userSelection'
  import type { Role, UserSelectionError } from '@/types/api'

  const store = useUserSelectionStore()
  const router = useRouter()

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
        router.push('/practice')
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
  background: var(--bg-primary);
  position: relative;
  overflow: hidden;
}

.content-wrapper {
  max-width: 520px;
  margin: 0 auto;
  padding: var(--space-10) var(--space-6);
  position: relative;
  z-index: 1;
}

h1 {
  margin-bottom: var(--space-8);
  color: var(--text-primary);
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
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
  color: var(--accent-primary);
  opacity: 0.15;
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
  gap: var(--space-4);
  padding: var(--space-12);
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-primary);
  border-top-color: var(--accent-primary);
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
  background: var(--bg-secondary);
  border-radius: var(--radius-2xl);
  padding: var(--space-8);
  box-shadow: var(--shadow-card);
  text-align: center;
}

.success-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--space-4);
  color: var(--color-success);
}

.success-icon svg {
  width: 100%;
  height: 100%;
}

.success-card h2 {
  margin: 0 0 var(--space-6);
  color: var(--text-primary);
  font-size: var(--text-2xl);
}

.success-details {
  text-align: left;
  background: var(--bg-tertiary);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
}

.success-details p {
  margin: var(--space-2) 0;
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.success-details p:first-child {
  margin-top: 0;
}

.success-details p:last-child {
  margin-bottom: 0;
}

.success-details strong {
  color: var(--text-secondary);
  font-weight: var(--font-medium);
}

/* Form cards */
.selection-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.form-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-2xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-subtle);
  transition:
    box-shadow var(--transition-base),
    border-color var(--transition-base);
}

.form-card:hover {
  box-shadow: var(--shadow-lg);
}

.form-card:focus-within {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow-sm);
}

/* Labels */
label {
  display: block;
  margin-bottom: var(--space-3);
  font-weight: var(--font-semibold);
  font-size: var(--text-sm);
  color: var(--text-primary);
}

/* Input fields */
input,
select,
textarea {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-family: inherit;
  box-sizing: border-box;
  background: var(--bg-input);
  color: var(--text-primary);
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

input::placeholder,
textarea::placeholder {
  color: var(--text-muted);
}

input:hover:not(:disabled),
select:hover:not(:disabled),
textarea:hover:not(:disabled) {
  border-color: var(--border-secondary);
}

input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px var(--accent-light);
}

input.error,
select.error,
textarea.error {
  border-color: var(--color-error);
}

input.error:focus,
select.error:focus,
textarea.error:focus {
  box-shadow: 0 0 0 3px var(--color-error-bg);
}

/* Select wrapper for custom arrow */
.select-wrapper {
  position: relative;
}

.select-wrapper select {
  appearance: none;
  padding-right: var(--space-10);
  cursor: pointer;
}

.select-arrow {
  position: absolute;
  right: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: var(--text-secondary);
  pointer-events: none;
  transition: color var(--transition-fast);
}

.select-wrapper:hover .select-arrow {
  color: var(--text-primary);
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
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: var(--space-2);
}

/* Error messages */
.error-message {
  display: block;
  color: var(--color-error-text);
  font-size: var(--text-sm);
  margin-top: var(--space-2);
  font-weight: var(--font-medium);
}

.submit-error {
  background: var(--color-error-bg);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-xl);
  padding: var(--space-4) var(--space-5);
  color: var(--color-error-text);
  font-size: var(--text-sm);
}

/* Submit button */
.submit-button {
  width: 100%;
  padding: var(--space-4) var(--space-6);
  background: var(--accent-primary);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-xl);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition:
    background var(--transition-fast),
    transform var(--transition-fast),
    box-shadow var(--transition-fast);
  box-shadow: 0 2px 8px var(--accent-glow);
}

.submit-button:hover:not(:disabled) {
  background: var(--accent-hover);
  box-shadow: var(--shadow-glow);
}

.submit-button:active:not(:disabled) {
  transform: translateY(1px);
}

.submit-button:disabled {
  background: var(--text-muted);
  cursor: not-allowed;
  box-shadow: none;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .content-wrapper {
    padding: var(--space-6) var(--space-4);
  }

  h1 {
    font-size: var(--text-2xl);
  }

  .form-card {
    padding: var(--space-5);
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
