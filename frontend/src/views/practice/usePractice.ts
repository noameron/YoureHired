import { ref } from 'vue'

export function useHints() {
  const expandedHints = ref<number[]>([])

  function toggleHint(index: number) {
    const idx = expandedHints.value.indexOf(index)
    if (idx > -1) {
      expandedHints.value.splice(idx, 1)
    } else {
      expandedHints.value.push(index)
    }
  }

  function isHintExpanded(index: number): boolean {
    return expandedHints.value.includes(index)
  }

  return {
    expandedHints,
    toggleHint,
    isHintExpanded,
  }
}

export function useSolution() {
  const solution = ref<string>('')

  function submitSolution() {
    // TODO: Wire up to backend API for solution feedback
    console.log('Solution submitted:', solution.value)
  }

  return {
    solution,
    submitSolution,
  }
}
