import { Calendar, RefreshCw, Users, Video } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { CRMSyncRecord, MeetingBooking } from '../../api/types'
import { EmptyState, InlineBanner, ListLoading, WsSearchInput } from '../workspace'
import { MeetingDetailPanel } from './MeetingDetailPanel'
import { MeetingRow } from './MeetingRow'

type MeetingInboxPanelProps = {
  meetings: MeetingBooking[]
  crmSyncs: CRMSyncRecord[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  bookDate: string
  bookTime: string
  onRetry: () => void
  onRequestBook: (id: string) => void
  onRetryCrm: (id: string) => void
  onSendReminder: (id: string, type: '24h' | '1h') => void
  onCancel: (id: string) => void
  actionPending: boolean
  onCreateRequest: () => void
  createPending: boolean
}

export function MeetingInboxPanel({
  meetings,
  crmSyncs,
  isLoading,
  isFetching,
  error,
  bookDate,
  bookTime,
  onRetry,
  onRequestBook,
  onRetryCrm,
  onSendReminder,
  onCancel,
  actionPending,
  onCreateRequest,
  createPending,
}: MeetingInboxPanelProps) {
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return meetings
    return meetings.filter((m) =>
      [m.contact_name, m.meeting_id, m.status, m.scheduled_at].filter(Boolean).join(' ').toLowerCase().includes(q),
    )
  }, [meetings, query])

  const selected = filtered.find((m) => m.meeting_id === selectedId) ?? filtered[0] ?? null

  const kpis = [
    { label: 'Meetings', value: String(meetings.length), hint: 'Total bookings', icon: Calendar },
    { label: 'Pending', value: String(meetings.filter((m) => ['draft', 'pending_approval'].includes(String(m.status))).length), hint: 'Awaiting approval', icon: Video },
    { label: 'CRM syncs', value: String(crmSyncs.length), hint: 'Sync records', icon: Users },
    { label: 'Failed', value: String(crmSyncs.filter((s) => s.status === 'failed').length), hint: 'Needs retry', icon: RefreshCw },
  ]

  return (
    <section className="sdr-split__right">
      <header className="sdr-split__right-header">
        <div>
          <p className="ws-heading-section">Inbox</p>
          <h2 className="sdr-split__pane-title">Meeting queue</h2>
          <p className="sdr-split__pane-desc">Approve bookings, send reminders, and monitor CRM sync.</p>
        </div>
        <button type="button" className="ws-btn ws-btn--secondary ws-btn--compact" disabled={isFetching} onClick={onRetry}>
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
          Refresh
        </button>
      </header>

      <div className="sdr-split__kpi-row">
        {kpis.map((kpi) => (
          <article key={kpi.label} className="sdr-split-kpi">
            <span className="sdr-split-kpi__icon" aria-hidden>
              <kpi.icon className="h-4 w-4" />
            </span>
            <p className="ws-kpi-label">{kpi.label}</p>
            <p className="ws-kpi-value">{kpi.value}</p>
            <p className="ws-kpi-hint">{kpi.hint}</p>
          </article>
        ))}
      </div>

      <div className="sdr-split__filters">
        <WsSearchInput value={query} onChange={setQuery} placeholder="Search meetings…" aria-label="Search meetings" />
      </div>

      <div className="sdr-split__master-detail">
        <div className="sdr-split__list-wrap">
          {error ? <InlineBanner message="Failed to load meetings" onRetry={onRetry} /> : null}

          {isLoading ? (
            <ListLoading rows={4} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<Calendar className="h-7 w-7" aria-hidden />}
              title={query ? 'No matching meetings' : 'No meetings'}
              description="Create a meeting request from a conversation."
              action={
                !query ? (
                  <button type="button" className="ws-btn ws-btn--primary" disabled={createPending} onClick={onCreateRequest}>
                    Create request
                  </button>
                ) : null
              }
            />
          ) : (
            <div className="sdr-split-row-list">
              {filtered.map((meeting) => (
                <MeetingRow
                  key={meeting.meeting_id}
                  meeting={meeting}
                  selected={selected?.meeting_id === meeting.meeting_id}
                  onSelect={() => setSelectedId(meeting.meeting_id)}
                />
              ))}
            </div>
          )}
        </div>

        {selected ? (
          <MeetingDetailPanel
            meeting={selected}
            bookDate={bookDate}
            bookTime={bookTime}
            crmSyncs={crmSyncs}
            onRequestBook={onRequestBook}
            onRetryCrm={onRetryCrm}
            onSendReminder={onSendReminder}
            onCancel={onCancel}
            actionPending={actionPending}
          />
        ) : (
          <aside className="sdr-split__detail sdr-split__detail--empty hidden xl:flex">
            <div className="sdr-split__detail-placeholder">
              <Calendar className="h-8 w-8" aria-hidden />
              <p>Select a meeting to approve, book, or manage CRM sync.</p>
            </div>
          </aside>
        )}
      </div>
    </section>
  )
}
