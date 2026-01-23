import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface UserSelectionState {
  companyName: string
  role: string
  roleDescription: string | null
  sessionId: string | null
}

export const useUserSelectionStore = defineStore('userSelection', () => {
  const companyName = ref('')
  const role = ref('')
  const roleDescription = ref<string | null>(null)
  const sessionId = ref<string | null>(null)

  const hasSelection = computed(() => {
    return companyName.value !== '' && role.value !== '' && sessionId.value !== null
  })

  function setSelection(selection: UserSelectionState) {
    companyName.value = selection.companyName
    role.value = selection.role
    roleDescription.value = selection.roleDescription
    sessionId.value = selection.sessionId
  }

  function clearSelection() {
    companyName.value = ''
    role.value = ''
    roleDescription.value = null
    sessionId.value = null
  }

  return {
    companyName,
    role,
    roleDescription,
    sessionId,
    hasSelection,
    setSelection,
    clearSelection
  }
})
