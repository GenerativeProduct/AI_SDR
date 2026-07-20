import type { ConversationThread } from '../../api/types'
import { RoleGuard } from '../auth/RoleGuard'
import { StatusBadge } from '../workspace'

type PendingAction = { action: 'approve' | 'send'; id: string }

type ConversationDetailPanelProps = {
  thread: ConversationThread
  onRequestAction: (pending: PendingAction) => void
  actionPending: boolean
}

export function ConversationDetailPanel({ thread, onRequestAction, actionPending }: ConversationDetailPanelProps) {
  return (
    <aside className="sdr-split__detail">
      <header className="sdr-split__detail-header">
        <div>
          <p className="ws-heading-section">Thread</p>
          <h2 className="sdr-split__pane-title">{thread.conversation_id}</h2>
          <p className="sdr-split__pane-desc">Review inbound message and approve or send the drafted reply.</p>
        </div>
        <StatusBadge status={String(thread.status)} />
      </header>

      <div className="sdr-split__detail-body">
        {thread.classification ? (
          <div className="sdr-split__meta-card">
            <p className="sdr-split__meta-card__label">Classification</p>
            <p className="mt-2 text-sm text-[var(--ws-text-secondary)]">{String(thread.classification)}</p>
          </div>
        ) : null}

        {thread.inbound_message ? (
          <section className="sdr-split__detail-section">
            <h3 className="sdr-split__detail-section__title">Inbound</h3>
            <p className="sdr-split__detail-section__body">{String(thread.inbound_message)}</p>
          </section>
        ) : null}

        {thread.draft_reply ? (
          <section className="sdr-split__detail-section sdr-split__detail-section--draft">
            <h3 className="sdr-split__detail-section__title">Draft reply</h3>
            <p className="sdr-split__detail-section__body sdr-split__detail-section__body--pre">
              {String(thread.draft_reply)}
            </p>
          </section>
        ) : null}

        <RoleGuard requireApprove>
          <div className="sdr-split__detail-actions">
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={actionPending}
              onClick={() => onRequestAction({ action: 'approve', id: thread.conversation_id })}
            >
              Approve reply
            </button>
            <button
              type="button"
              className="ws-btn ws-btn--primary"
              disabled={actionPending}
              onClick={() => onRequestAction({ action: 'send', id: thread.conversation_id })}
            >
              Send reply
            </button>
          </div>
        </RoleGuard>
      </div>
    </aside>
  )
}

export type { PendingAction }
