import { UserRound } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { ProspectIntelligenceResult } from '../../api/types'
import { bandTone, formatPct, scoreTone } from './intelligenceUtils'

type IntelligenceResultRowProps = {
  row: ProspectIntelligenceResult
  selected: boolean
  onSelect: () => void
}

export function IntelligenceResultRow({ row, selected, onSelect }: IntelligenceResultRowProps) {
  const band = bandTone(row.ranking.priority_band)
  const scoreToneKey = scoreTone(row.ranking.priority_score)
  const scoreWidth = Math.min(100, Math.max(8, Math.round((row.ranking.priority_score / 10) * 100)))

  return (
    <button
      type="button"
      className={cn('sdr-intelligence-result ws-focus-ring', selected && 'sdr-intelligence-result--active')}
      onClick={onSelect}
    >
      <span className="sdr-intelligence-result__icon" aria-hidden>
        <UserRound className="h-4 w-4" />
      </span>
      <span className="sdr-intelligence-result__copy min-w-0">
        <span className="sdr-intelligence-result__head">
          <span className="sdr-intelligence-result__name">
            {row.contact_name} @ {row.company_name}
          </span>
          <span className={cn('sdr-intelligence-result__band', `sdr-intelligence-result__band--${band}`)}>
            {row.ranking.priority_band}
          </span>
        </span>
        <span className="sdr-intelligence-result__meta">
          Intent {row.intent.level} · Reply {formatPct(row.propensity.reply_probability.value)}
        </span>
        <span className="sdr-intelligence-result__fit">
          <span className="sdr-intelligence-result__fit-label">Priority</span>
          <span className={cn('sdr-intelligence-result__fit-value', `sdr-intelligence-result__fit-value--${scoreToneKey}`)}>
            {row.ranking.priority_score.toFixed(1)}
          </span>
          <span className="sdr-intelligence-result__fit-track" aria-hidden>
            <span
              className={cn('sdr-intelligence-result__fit-fill', `sdr-intelligence-result__fit-fill--${scoreToneKey}`)}
              style={{ width: `${scoreWidth}%` }}
            />
          </span>
        </span>
      </span>
    </button>
  )
}
