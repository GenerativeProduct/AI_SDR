import type { CRMSyncRecord, MeetingBooking } from '../../api/types'
import { RoleGuard } from '../auth/RoleGuard'
import { StatusBadge } from '../workspace'
import { formatDate } from '../../lib/utils'

type MeetingDetailPanelProps = {
  meeting: MeetingBooking
  bookDate: string
  bookTime: string
  crmSyncs: CRMSyncRecord[]
  onRequestBook: (id: string) => void
  onRetryCrm: (id: string) => void
  onSendReminder: (id: string, type: '24h' | '1h') => void
  onCancel: (id: string) => void
  actionPending: boolean
}

export function MeetingDetailPanel({
  meeting,
  bookDate,
  bookTime,
  crmSyncs,
  onRequestBook,
  onRetryCrm,
  onSendReminder,
  onCancel,
  actionPending,
}: MeetingDetailPanelProps) {
  const status = String(meeting.status)
  const relatedSyncs = crmSyncs.filter((s) => s.meeting_id === meeting.meeting_id)

  return (
    <aside className="sdr-split__detail">
      <header className="sdr-split__detail-header">
        <div>
          <p className="ws-heading-section">Meeting brief</p>
          <h2 className="sdr-split__pane-title">{meeting.contact_name ?? meeting.meeting_id}</h2>
          <p className="sdr-split__pane-desc">{formatDate(meeting.scheduled_at) || 'Not scheduled'}</p>
        </div>
        <StatusBadge status={status} />
      </header>

      <div className="sdr-split__detail-body">
        <RoleGuard requireApprove>
          <div className="sdr-split__detail-actions !mt-0">
            {['draft', 'pending_approval'].includes(status) ? (
              <button
                type="button"
                className="ws-btn ws-btn--primary"
                disabled={!bookDate || actionPending}
                onClick={() => onRequestBook(meeting.meeting_id)}
              >
                Approve & book
              </button>
            ) : null}
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={actionPending}
              onClick={() => onRetryCrm(meeting.meeting_id)}
            >
              Retry CRM
            </button>
            <button
              type="button"
              className="ws-btn ws-btn--ghost"
              disabled={actionPending}
              onClick={() => onSendReminder(meeting.meeting_id, '24h')}
            >
              24h reminder
            </button>
            <button
              type="button"
              className="ws-btn ws-btn--ghost"
              disabled={actionPending}
              onClick={() => onCancel(meeting.meeting_id)}
            >
              Cancel
            </button>
          </div>
        </RoleGuard>

        {bookDate ? (
          <section className="sdr-split__detail-section">
            <h3 className="sdr-split__detail-section__title">Pending booking</h3>
            <p className="sdr-split__detail-section__body">
              {bookDate} at {bookTime} UTC · 30 min
            </p>
          </section>
        ) : null}

        <section className="sdr-split__detail-section">
          <h3 className="sdr-split__detail-section__title">CRM syncs</h3>
          {relatedSyncs.length === 0 ? (
            <p className="sdr-split__detail-section__body">No sync records for this meeting.</p>
          ) : (
            <ul className="mt-2 space-y-2 text-sm">
              {relatedSyncs.map((sync) => (
                <li key={sync.sync_id ?? sync.meeting_id} className="flex items-center justify-between gap-2">
                  <span className="capitalize">{sync.provider}</span>
                  <StatusBadge status={sync.status} />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </aside>
  )
}
