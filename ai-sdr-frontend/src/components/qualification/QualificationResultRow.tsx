import { FlaskConical } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { QualificationResult } from '../../api/types'
import { QualificationBadge } from '../workspace'
import { qualificationKey } from './qualificationUtils'

type QualificationResultRowProps = {
  row: QualificationResult
  selected: boolean
  onSelect: () => void
}

export function QualificationResultRow({ row, selected, onSelect }: QualificationResultRowProps) {
  const scorePct = Math.min(100, Math.round(row.qualification_score))

  return (
    <button
      type="button"
      className={cn('sdr-qualification-result ws-focus-ring', selected && 'sdr-qualification-result--active')}
      onClick={onSelect}
    >
      <span className="sdr-qualification-result__icon" aria-hidden>
        <FlaskConical className="h-4 w-4" />
      </span>
      <span className="sdr-qualification-result__copy min-w-0">
        <span className="sdr-qualification-result__head">
          <span className="sdr-qualification-result__name">
            {row.contact_name} @ {row.company_name}
          </span>
          <QualificationBadge tier={row.qualification_status} />
        </span>
        <span className="sdr-qualification-result__meta">{row.next_action}</span>
        <span className="sdr-qualification-result__score-row">
          <span className="sdr-qualification-result__score-label">Score {scorePct}</span>
          <span className="sdr-qualification-result__track" aria-hidden>
            <span className="sdr-qualification-result__fill" style={{ width: `${scorePct}%` }} />
          </span>
        </span>
      </span>
    </button>
  )
}

export { qualificationKey }
