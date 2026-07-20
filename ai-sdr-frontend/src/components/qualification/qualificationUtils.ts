import type { QualificationResult } from '../../api/types'

export function formatCount(value: number) {
  return value.toLocaleString()
}

export function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`
}

export function qualificationKey(row: QualificationResult) {
  return row.qualification_id ?? row.contact_id
}

export function countByStatus(results: QualificationResult[], status: QualificationResult['qualification_status']) {
  return results.filter((row) => row.qualification_status === status).length
}

export function salesReadyCount(results: QualificationResult[]) {
  return results.filter((row) => row.sales_ready).length
}

export function averageQualificationScore(results: QualificationResult[]) {
  if (!results.length) return 0
  const total = results.reduce((sum, row) => sum + row.qualification_score, 0)
  return Math.round(total / results.length)
}

export const QUALIFICATION_FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'SQL', label: 'SQL' },
  { id: 'MQL', label: 'MQL' },
  { id: 'Nurture', label: 'Nurture' },
  { id: 'Disqualified', label: 'Disqualified' },
] as const
