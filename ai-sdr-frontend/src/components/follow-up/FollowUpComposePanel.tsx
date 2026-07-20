import { Loader2, Plus } from 'lucide-react'
import { WorkspaceField, WorkspaceSelect } from '../workspace'

type SelectOption = { value: string; label: string }

type FollowUpComposePanelProps = {
  campaignId: string
  contactId: string
  campaignOptions: SelectOption[]
  schedulerBackend?: string
  onCampaignChange: (value: string) => void
  onContactChange: (value: string) => void
  onCreate: () => void
  createPending: boolean
}

export function FollowUpComposePanel({
  campaignId,
  contactId,
  campaignOptions,
  schedulerBackend,
  onCampaignChange,
  onContactChange,
  onCreate,
  createPending,
}: FollowUpComposePanelProps) {
  return (
    <aside className="sdr-split__left">
      <header className="sdr-split__left-header">
        <div>
          <p className="ws-heading-section">Compose</p>
          <h2 className="sdr-split__pane-title">New follow-up plan</h2>
          <p className="sdr-split__pane-desc">Multi-touch sequences after outreach campaigns.</p>
        </div>
        {schedulerBackend ? (
          <span className="sdr-split__status-chip sdr-split__status-chip--on">{schedulerBackend}</span>
        ) : null}
      </header>

      <div className="sdr-split__left-body">
        <div className="sdr-split__meta-card">
          <p className="sdr-split__meta-card__label">Plan defaults</p>
          <dl className="sdr-split__meta-dl">
            <div>
              <dt>Approval</dt>
              <dd>Required before send</dd>
            </div>
            <div>
              <dt>Scheduler</dt>
              <dd>{schedulerBackend ?? 'local'}</dd>
            </div>
          </dl>
        </div>

        <div className="sdr-split__form">
          <WorkspaceSelect
            id="fu-campaign"
            label="Campaign"
            value={campaignId}
            options={campaignOptions}
            onChange={onCampaignChange}
            placeholder="Select campaign…"
          />
          <WorkspaceField
            id="fu-contact"
            label="Contact ID"
            value={contactId}
            onChange={onContactChange}
            placeholder="contact_…"
          />
        </div>

        <button
          type="button"
          className="ws-btn ws-btn--primary w-full"
          disabled={!campaignId || !contactId || createPending}
          onClick={onCreate}
        >
          {createPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Plus className="h-4 w-4" aria-hidden />}
          Create plan
        </button>
      </div>
    </aside>
  )
}
