import { ref } from 'vue'
import type { Ref } from 'vue'

export function useExpandableList(): {
  expanded: Ref<number[]>
  toggle: (index: number) => void
  isExpanded: (index: number) => boolean
  reset: () => void
} {
  const expanded = ref<number[]>([])

  function toggle(index: number): void {
    const idx = expanded.value.indexOf(index)
    if (idx > -1) {
      expanded.value.splice(idx, 1)
    } else {
      expanded.value.push(index)
    }
  }

  function isExpanded(index: number): boolean {
    return expanded.value.includes(index)
  }

  function reset(): void {
    expanded.value = []
  }

  return { expanded, toggle, isExpanded, reset }
}
