import type { EnrichmentResult } from '../../api/types'

export function formatCount(value: number) {
  return value.toLocaleString()
}

export function formatConfidence(score: number) {
  return `${Math.round(score * 100)}%`
}

export function averageConfidence(results: EnrichmentResult[]) {
  if (!results.length) return 0
  const total = results.reduce((sum, result) => sum + result.confidence_score, 0)
  return Math.round((total / results.length) * 100)
}

export function highConfidenceCount(results: EnrichmentResult[], threshold = 0.7) {
  return results.filter((result) => result.confidence_score >= threshold).length
}

export function resultsWithSignals(results: EnrichmentResult[]) {
  return results.filter((result) => (result.signals?.length ?? 0) > 0).length
}

export function confidenceTone(score: number): 'success' | 'risk' | 'default' {
  if (score >= 0.7) return 'success'
  if (score < 0.45) return 'risk'
  return 'default'
}
