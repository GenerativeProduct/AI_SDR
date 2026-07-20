import { format, parseISO } from 'date-fns'
import type { FollowUpPlan, FollowUpTouch } from '../../api/types'
import { RoleGuard } from '../auth/RoleGuard'
import { StatusBadge } from '../workspace'

type FollowUpDetailPanelProps = {
  plan: FollowUpPlan
  onApprove: () => void
  approvePending: boolean
}

function TouchTimelineItem({ touch }: { touch: FollowUpTouch }) {
  return (
    <div className="sdr-split__timeline-item">
      <div className="sdr-split__detail-section !p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-sm font-semibold text-[var(--ws-text-primary)]">Step {touch.sequence_order}</span>
          <StatusBadge status={touch.status} />
        </div>
        <p className="mt-1 text-xs text-[var(--ws-text-muted)]">
          {touch.channel} · {touch.delay_hours}h delay · {format(parseISO(touch.scheduled_at), 'MMM d, h:mm a')}
        </p>
        {touch.subject ? <p className="mt-1 text-sm font-medium text-[var(--ws-text-primary)]">{touch.subject}</p> : null}
        <p className="mt-2 whitespace-pre-wrap text-sm text-[var(--ws-text-secondary)]">{touch.body}</p>
      </div>
    </div>
  )
}

export function FollowUpDetailPanel({ plan, onApprove, approvePending }: FollowUpDetailPanelProps) {
  const touches = [...(plan.touches ?? [])].sort((a, b) => a.sequence_order - b.sequence_order)

  return (
    <aside className="sdr-split__detail">
      <header className="sdr-split__detail-header">
        <div>
          <p className="ws-heading-section">Plan brief</p>
          <h2 className="sdr-split__pane-title">Contact {plan.contact_id}</h2>
          <p className="sdr-split__pane-desc">Campaign {plan.campaign_id}</p>
        </div>
        <StatusBadge status={plan.status} />
      </header>

      <div className="sdr-split__detail-body">
        {plan.status === 'pending_approval' ? (
          <RoleGuard requireApprove>
            <button
              type="button"
              className="ws-btn ws-btn--primary w-full"
              disabled={approvePending}
              onClick={onApprove}
            >
              Approve plan
            </button>
          </RoleGuard>
        ) : null}

        {touches.length ? (
          <section>
            <h3 className="sdr-split__detail-section__title">Touch timeline</h3>
            <div className="sdr-split__timeline">
              {touches.map((touch) => (
                <TouchTimelineItem key={touch.touch_id ?? touch.sequence_order} touch={touch} />
              ))}
            </div>
          </section>
        ) : (
          <p className="text-sm text-[var(--ws-text-muted)]">No touchpoints generated yet.</p>
        )}
      </div>
    </aside>
  )
}
