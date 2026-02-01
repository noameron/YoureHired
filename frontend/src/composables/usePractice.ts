import { ref } from 'vue'
import { submitSolution as apiSubmitSolution } from '@/services/api'
import type { SolutionFeedback } from '@/services/types'
import { useExpandableList } from './useExpandableList'

export function useHints() {
  const { expanded: expandedHints, toggle: toggleHint, isExpanded: isHintExpanded } = useExpandableList()

  return {
    expandedHints,
    toggleHint,
    isHintExpanded,
  }
}

export function useSolution(sessionId: () => string | null) {
  const solution = ref<string>('')
  const feedback = ref<SolutionFeedback | null>(null)
  const isEvaluating = ref<boolean>(false)
  const evaluationError = ref<string | null>(null)

  async function submitSolution() {
    const sid = sessionId()
    if (!sid || !solution.value.trim()) {
      return
    }

    isEvaluating.value = true
    evaluationError.value = null

    try {
      const result = await apiSubmitSolution(sid, solution.value)

      if (result.success) {
        feedback.value = result.data.feedback
      } else {
        evaluationError.value = result.error.message
      }
    } catch (e) {
      evaluationError.value = e instanceof Error ? e.message : 'Evaluation failed'
    } finally {
      isEvaluating.value = false
    }
  }

  function clearFeedback() {
    feedback.value = null
    evaluationError.value = null
  }

  return {
    solution,
    feedback,
    isEvaluating,
    evaluationError,
    submitSolution,
    clearFeedback,
  }
}
