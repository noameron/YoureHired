export type ScoreCategory = 'good' | 'adequate' | 'needs-work'

export function getScoreColor(score: number): ScoreCategory {
  if (score >= 7) return 'good'
  if (score >= 5) return 'adequate'
  return 'needs-work'
}

export function getScoreLabel(score: number): string {
  if (score >= 9) return 'Exceptional'
  if (score >= 7) return 'Good'
  if (score >= 5) return 'Adequate'
  if (score >= 3) return 'Needs Work'
  return 'Incomplete'
}
