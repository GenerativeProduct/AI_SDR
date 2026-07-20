import type { ProspectIntelligenceResult } from '../../api/types'

export function formatCount(value: number) {
  return value.toLocaleString()
}

export function formatPct(value: number) {
  return `${Math.round(value * 100)}%`
}

export function averagePriorityScore(rows: ProspectIntelligenceResult[]) {
  if (rows.length === 0) return 0
  const total = rows.reduce((sum, row) => sum + row.ranking.priority_score, 0)
  return Math.round((total / rows.length) * 10) / 10
}

export function highPriorityCount(rows: ProspectIntelligenceResult[]) {
  return rows.filter((row) => row.ranking.priority_band === 'high').length
}

export function highIntentCount(rows: ProspectIntelligenceResult[]) {
  return rows.filter((row) => row.intent.level === 'high').length
}

export function bandTone(band: 'high' | 'medium' | 'low'): 'success' | 'default' | 'risk' {
  if (band === 'high') return 'success'
  if (band === 'low') return 'risk'
  return 'default'
}

export function levelTone(level: 'high' | 'medium' | 'low'): 'success' | 'default' | 'risk' {
  return bandTone(level)
}

export function scoreTone(score: number): 'success' | 'default' | 'risk' {
  if (score >= 7) return 'success'
  if (score < 4) return 'risk'
  return 'default'
}
