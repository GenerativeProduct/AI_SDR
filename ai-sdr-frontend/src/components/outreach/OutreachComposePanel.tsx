import { Clock, Loader2, MailPlus, UserRound } from 'lucide-react'
import type { DiscoveredContact } from '../../api/types'
import { RoleGuard } from '../auth/RoleGuard'
import { WorkspaceSelect } from '../workspace'

type SelectOption = { value: string; label: string }

type OutreachComposePanelProps = {
  contactId: string
  channel: string
  contactOptions: SelectOption[]
  selectedContact?: DiscoveredContact
  onContactChange: (value: string) => void
  onChannelChange: (value: string) => void
  onCreate: () => void
  createPending: boolean
  onRunScheduler: () => void
  schedulerPending: boolean
}

const CHANNEL_OPTIONS = [
  { value: 'email', label: 'Email' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'phone', label: 'Phone' },
]

export function OutreachComposePanel({
  contactId,
  channel,
  contactOptions,
  selectedContact,
  onContactChange,
  onChannelChange,
  onCreate,
  createPending,
  onRunScheduler,
  schedulerPending,
}: OutreachComposePanelProps) {
  return (
    <aside className="sdr-outreach__compose">
      <header className="sdr-outreach__compose-header">
        <div>
          <p className="ws-heading-section">Compose</p>
          <h2 className="sdr-outreach__pane-title">New campaign</h2>
          <p className="sdr-outreach__pane-desc">
            Draft a multi-touch sequence with approval gates before send.
          </p>
        </div>
      </header>

      <div className="sdr-outreach__compose-body">
        <div className="sdr-outreach__cadence-card">
          <p className="sdr-outreach__cadence-card__label">Default cadence</p>
          <dl className="sdr-outreach__cadence-meta">
            <div>
              <dt>Touches</dt>
              <dd>3</dd>
            </div>
            <div>
              <dt>Spacing</dt>
              <dd>48 hours</dd>
            </div>
            <div>
              <dt>Approval</dt>
              <dd>Required</dd>
            </div>
          </dl>
        </div>

        <div className="sdr-outreach__form">
          <WorkspaceSelect
            id="outreach-contact"
            label="Contact"
            value={contactId}
            options={contactOptions}
            onChange={onContactChange}
            placeholder="Select contact…"
          />

          <WorkspaceSelect
            id="outreach-channel"
            label="Channel"
            value={channel}
            options={CHANNEL_OPTIONS}
            onChange={onChannelChange}
          />

          {selectedContact ? (
            <div className="sdr-outreach__contact-preview">
              <span className="sdr-outreach__contact-preview__icon" aria-hidden>
                <UserRound className="h-4 w-4" />
              </span>
              <div className="min-w-0">
                <p className="sdr-outreach__contact-preview__name">{selectedContact.full_name}</p>
                <p className="sdr-outreach__contact-preview__meta">{selectedContact.title}</p>
              </div>
            </div>
          ) : null}
        </div>

        <button
          type="button"
          className="ws-btn ws-btn--primary w-full"
          disabled={!contactId || createPending}
          onClick={onCreate}
        >
          {createPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <MailPlus className="h-4 w-4" aria-hidden />}
          Create campaign
        </button>

        <RoleGuard requireApprove>
          <button
            type="button"
            className="ws-btn ws-btn--secondary w-full"
            disabled={schedulerPending}
            onClick={onRunScheduler}
          >
            {schedulerPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Clock className="h-4 w-4" aria-hidden />}
            Run due scheduler
          </button>
        </RoleGuard>
      </div>
    </aside>
  )
}
