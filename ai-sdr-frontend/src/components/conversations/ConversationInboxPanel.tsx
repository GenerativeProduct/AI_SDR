import { MessageSquare, RefreshCw } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { ConversationThread } from '../../api/types'
import { EmptyState, InlineBanner, ListLoading, WsSearchInput } from '../workspace'
import { ConversationDetailPanel, type PendingAction } from './ConversationDetailPanel'
import { ConversationThreadRow } from './ConversationThreadRow'

type ConversationInboxPanelProps = {
  threads: ConversationThread[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  onRetry: () => void
  onRequestAction: (pending: PendingAction) => void
  actionPending: boolean
}

export function ConversationInboxPanel({
  threads,
  isLoading,
  isFetching,
  error,
  onRetry,
  onRequestAction,
  actionPending,
}: ConversationInboxPanelProps) {
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return threads
    return threads.filter((thread) =>
      [thread.conversation_id, thread.status, thread.inbound_message, thread.classification]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
        .includes(q),
    )
  }, [threads, query])

  const selected = filtered.find((t) => t.conversation_id === selectedId) ?? filtered[0] ?? null

  return (
    <section className="sdr-split__right">
      <header className="sdr-split__right-header">
        <div>
          <p className="ws-heading-section">Inbox</p>
          <h2 className="sdr-split__pane-title">Conversation threads</h2>
          <p className="sdr-split__pane-desc">Inbound replies awaiting review and operator approval.</p>
        </div>
        <button type="button" className="ws-btn ws-btn--secondary ws-btn--compact" disabled={isFetching} onClick={onRetry}>
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
          Refresh
        </button>
      </header>

      <div className="sdr-split__filters">
        <WsSearchInput value={query} onChange={setQuery} placeholder="Search threads…" aria-label="Search conversations" />
      </div>

      <div className="sdr-split__master-detail">
        <div className="sdr-split__list-wrap">
          {error ? <InlineBanner message="Failed to load conversations" onRetry={onRetry} /> : null}

          {isLoading ? (
            <ListLoading rows={6} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<MessageSquare className="h-7 w-7" aria-hidden />}
              title={query ? 'No matching threads' : 'No threads'}
              description={query ? 'Try a different search.' : 'Simulate inbound or wait for replies.'}
            />
          ) : (
            <div className="sdr-split-row-list">
              {filtered.map((thread) => (
                <ConversationThreadRow
                  key={thread.conversation_id}
                  thread={thread}
                  selected={selected?.conversation_id === thread.conversation_id}
                  onSelect={() => setSelectedId(thread.conversation_id)}
                />
              ))}
            </div>
          )}
        </div>

        {selected ? (
          <ConversationDetailPanel
            thread={selected}
            onRequestAction={onRequestAction}
            actionPending={actionPending}
          />
        ) : (
          <aside className="sdr-split__detail sdr-split__detail--empty hidden xl:flex">
            <div className="sdr-split__detail-placeholder">
              <MessageSquare className="h-8 w-8" aria-hidden />
              <p>Select a thread to review the inbound message and draft reply.</p>
            </div>
          </aside>
        )}
      </div>
    </section>
  )
}
