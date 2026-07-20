import { formatDistanceToNow, parseISO } from 'date-fns'
import { RefreshCw, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { CRMSyncRecord } from '../../api/types'
import { EmptyState, InlineBanner, ListLoading, StatusBadge, WsSearchInput } from '../workspace'

type CrmSyncPanelProps = {
  records: CRMSyncRecord[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  onRetry: () => void
  onRetrySync: (meetingId: string) => void
  retryPending: boolean
}

export function CrmSyncPanel({
  records,
  isLoading,
  isFetching,
  error,
  onRetry,
  onRetrySync,
  retryPending,
}: CrmSyncPanelProps) {
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return records
    return records.filter((r) =>
      [r.provider, r.meeting_id, r.status, r.sync_id].filter(Boolean).join(' ').toLowerCase().includes(q),
    )
  }, [records, query])

  const failedCount = records.filter((r) => r.status === 'failed').length

  return (
    <section className="sdr-split__right">
      <header className="sdr-split__right-header">
        <div>
          <p className="ws-heading-section">Audit log</p>
          <h2 className="sdr-split__pane-title">Sync records</h2>
          <p className="sdr-split__pane-desc">
            {records.length} total · {failedCount} failed
          </p>
        </div>
        <button type="button" className="ws-btn ws-btn--secondary ws-btn--compact" disabled={isFetching} onClick={onRetry}>
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
          Refresh
        </button>
      </header>

      <div className="sdr-split__filters">
        <WsSearchInput value={query} onChange={setQuery} placeholder="Search syncs…" aria-label="Search CRM syncs" />
      </div>

      <div className="sdr-split__canvas-scroll">
        {error ? <InlineBanner message="Failed to load syncs" onRetry={onRetry} /> : null}

        {isLoading ? (
          <ListLoading rows={5} />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<Users className="h-7 w-7" aria-hidden />}
            title={query ? 'No matching records' : 'No CRM sync records'}
            description="Book a meeting to trigger CRM sync."
          />
        ) : (
          <div className="sdr-split__canvas-card !p-0 overflow-hidden">
            <div className="sdr-split__table-wrap">
              <table className="sdr-split__table">
                <thead>
                  <tr>
                    <th>Provider</th>
                    <th>Meeting</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((record) => (
                    <tr key={record.sync_id ?? record.meeting_id}>
                      <td className="capitalize font-medium text-[var(--ws-text-primary)]">{record.provider}</td>
                      <td className="font-mono text-xs">{record.meeting_id}</td>
                      <td>
                        <StatusBadge status={record.status} />
                      </td>
                      <td className="text-xs">
                        {record.created_at
                          ? formatDistanceToNow(parseISO(record.created_at), { addSuffix: true })
                          : '—'}
                      </td>
                      <td>
                        {record.status === 'failed' ? (
                          <button
                            type="button"
                            className="ws-btn ws-btn--secondary ws-btn--compact"
                            disabled={retryPending}
                            onClick={() => onRetrySync(record.meeting_id)}
                          >
                            Retry
                          </button>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
