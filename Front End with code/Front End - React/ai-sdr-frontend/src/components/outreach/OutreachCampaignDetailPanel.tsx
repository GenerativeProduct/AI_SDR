import type { OutreachCampaign } from '../../api/types'
import { RoleGuard } from '../auth/RoleGuard'
import { CampaignChannelBadge, StatusBadge } from '../workspace'

type PendingAction = { action: 'approve' | 'send'; id: string; label: string }

type OutreachCampaignDetailPanelProps = {
  campaign: OutreachCampaign
  onRequestAction: (pending: PendingAction) => void
  onPause: (id: string) => void
  onResume: (id: string) => void
  onCancel: (id: string) => void
  actionPending: boolean
}

export function OutreachCampaignDetailPanel({
  campaign,
  onRequestAction,
  onPause,
  onResume,
  onCancel,
  actionPending,
}: OutreachCampaignDetailPanelProps) {
  const status = String(campaign.status)
  const label = String(campaign.contact_name ?? campaign.campaign_id)

  return (
    <aside className="sdr-outreach__detail">
      <header className="sdr-outreach__detail-header">
        <div>
          <p className="ws-heading-section">Campaign brief</p>
          <h2 className="sdr-outreach__pane-title">{label}</h2>
          <p className="sdr-outreach__pane-desc">Review copy, approve, and send or manage lifecycle.</p>
        </div>
        <div className="sdr-outreach__detail-badges">
          <StatusBadge status={status} />
          {campaign.channel ? <CampaignChannelBadge channel={String(campaign.channel)} /> : null}
        </div>
      </header>

      <div className="sdr-outreach__detail-body">
        {campaign.subject ? (
          <section className="sdr-outreach__detail-section">
            <h3 className="sdr-outreach__detail-section__title">Subject</h3>
            <p className="sdr-outreach__detail-section__body">{campaign.subject}</p>
          </section>
        ) : null}

        {campaign.body ? (
          <section className="sdr-outreach__detail-section">
            <h3 className="sdr-outreach__detail-section__title">Body</h3>
            <p className="sdr-outreach__detail-section__body sdr-outreach__detail-section__body--pre">
              {String(campaign.body)}
            </p>
          </section>
        ) : (
          <p className="sdr-outreach__empty-copy">No message body generated yet.</p>
        )}

        <RoleGuard requireApprove>
          <div className="sdr-outreach__detail-actions">
            {status === 'pending_approval' ? (
              <button
                type="button"
                className="ws-btn ws-btn--primary"
                disabled={actionPending}
                onClick={() =>
                  onRequestAction({ action: 'approve', id: campaign.campaign_id, label })
                }
              >
                Approve
              </button>
            ) : null}
            {['approved', 'running', 'paused'].includes(status) ? (
              <button
                type="button"
                className="ws-btn ws-btn--primary"
                disabled={actionPending}
                onClick={() => onRequestAction({ action: 'send', id: campaign.campaign_id, label })}
              >
                Send
              </button>
            ) : null}
            {status === 'running' ? (
              <button
                type="button"
                className="ws-btn ws-btn--secondary"
                disabled={actionPending}
                onClick={() => onPause(campaign.campaign_id)}
              >
                Pause
              </button>
            ) : null}
            {status === 'paused' ? (
              <button
                type="button"
                className="ws-btn ws-btn--secondary"
                disabled={actionPending}
                onClick={() => onResume(campaign.campaign_id)}
              >
                Resume
              </button>
            ) : null}
            {['pending_approval', 'approved', 'running', 'paused'].includes(status) ? (
              <button
                type="button"
                className="ws-btn ws-btn--ghost"
                disabled={actionPending}
                onClick={() => onCancel(campaign.campaign_id)}
              >
                Cancel
              </button>
            ) : null}
          </div>
        </RoleGuard>
      </div>
    </aside>
  )
}

export type { PendingAction }
