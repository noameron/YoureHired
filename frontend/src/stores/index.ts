import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const isLoading = ref(false)

  return { isLoading }
})

export { useUserSelectionStore } from './userSelection'
