import { Building2 } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { EnrichmentResult } from '../../api/types'
import { StatusBadge } from '../workspace'
import { confidenceTone, formatConfidence } from './enrichmentUtils'

type EnrichmentResultRowProps = {
  result: EnrichmentResult
  selected: boolean
  onSelect: () => void
}

export function EnrichmentResultRow({ result, selected, onSelect }: EnrichmentResultRowProps) {
  const tone = confidenceTone(result.confidence_score)
  const pct = Math.round(result.confidence_score * 100)

  return (
    <button
      type="button"
      className={cn('sdr-enrichment-result ws-focus-ring', selected && 'sdr-enrichment-result--active')}
      onClick={onSelect}
    >
      <span className="sdr-enrichment-result__icon" aria-hidden>
        <Building2 className="h-4 w-4" />
      </span>
      <span className="sdr-enrichment-result__copy min-w-0">
        <span className="sdr-enrichment-result__head">
          <span className="sdr-enrichment-result__name">{result.company_name}</span>
          <StatusBadge status={result.status} />
        </span>
        <span className="sdr-enrichment-result__meta">{result.recommended_next_action}</span>
        <span className="sdr-enrichment-result__fit">
          <span className="sdr-enrichment-result__fit-label">Confidence</span>
          <span className={cn('sdr-enrichment-result__fit-value', `sdr-enrichment-result__fit-value--${tone}`)}>
            {formatConfidence(result.confidence_score)}
          </span>
          <span className="sdr-enrichment-result__fit-track" aria-hidden>
            <span className={cn('sdr-enrichment-result__fit-fill', `sdr-enrichment-result__fit-fill--${tone}`)} style={{ width: `${pct}%` }} />
          </span>
        </span>
      </span>
    </button>
  )
}
