import { Repeat } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { FollowUpPlan } from '../../api/types'
import { StatusBadge } from '../workspace'

type FollowUpPlanRowProps = {
  plan: FollowUpPlan
  selected: boolean
  onSelect: () => void
}

export function FollowUpPlanRow({ plan, selected, onSelect }: FollowUpPlanRowProps) {
  const touchCount = plan.touches?.length ?? 0

  return (
    <button
      type="button"
      className={cn('sdr-split-row ws-focus-ring', selected && 'sdr-split-row--active')}
      onClick={onSelect}
    >
      <span className="sdr-split-row__icon" aria-hidden>
        <Repeat className="h-4 w-4" />
      </span>
      <span className="sdr-split-row__copy">
        <span className="sdr-split-row__head">
          <span className="sdr-split-row__name">Contact {plan.contact_id}</span>
          <StatusBadge status={plan.status} />
        </span>
        <span className="sdr-split-row__meta">
          Campaign {plan.campaign_id} · {touchCount} touch{touchCount === 1 ? '' : 'es'}
        </span>
      </span>
    </button>
  )
}
