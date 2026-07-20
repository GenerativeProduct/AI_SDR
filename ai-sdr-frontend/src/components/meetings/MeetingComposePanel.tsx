import { Loader2, Plus } from 'lucide-react'
import { WorkspaceField, WorkspaceSelect } from '../workspace'

type SelectOption = { value: string; label: string }

type MeetingComposePanelProps = {
  conversationId: string
  conversationOptions: SelectOption[]
  bookDate: string
  bookTime: string
  onConversationChange: (value: string) => void
  onBookDateChange: (value: string) => void
  onBookTimeChange: (value: string) => void
  onCreateRequest: () => void
  createPending: boolean
}

export function MeetingComposePanel({
  conversationId,
  conversationOptions,
  bookDate,
  bookTime,
  onConversationChange,
  onBookDateChange,
  onBookTimeChange,
  onCreateRequest,
  createPending,
}: MeetingComposePanelProps) {
  return (
    <aside className="sdr-split__left">
      <header className="sdr-split__left-header">
        <div>
          <p className="ws-heading-section">Compose</p>
          <h2 className="sdr-split__pane-title">Meeting requests</h2>
          <p className="sdr-split__pane-desc">Create requests from conversations and set booking defaults.</p>
        </div>
      </header>

      <div className="sdr-split__left-body">
        <div className="sdr-split__meta-card">
          <p className="sdr-split__meta-card__label">Booking defaults</p>
          <dl className="sdr-split__meta-dl">
            <div>
              <dt>Duration</dt>
              <dd>30 minutes</dd>
            </div>
            <div>
              <dt>Timezone</dt>
              <dd>UTC</dd>
            </div>
          </dl>
        </div>

        <div className="sdr-split__form">
          <WorkspaceSelect
            id="meeting-conversation"
            label="Conversation"
            value={conversationId}
            options={conversationOptions}
            onChange={onConversationChange}
            placeholder="Select conversation…"
          />
          <WorkspaceField
            id="book-date"
            label="Book date"
            value={bookDate}
            onChange={onBookDateChange}
            placeholder="YYYY-MM-DD"
          />
          <WorkspaceField id="book-time" label="Book time (UTC)" value={bookTime} onChange={onBookTimeChange} />
        </div>

        <button
          type="button"
          className="ws-btn ws-btn--primary w-full"
          disabled={!conversationId || createPending}
          onClick={onCreateRequest}
        >
          {createPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Plus className="h-4 w-4" aria-hidden />}
          Create request
        </button>
      </div>
    </aside>
  )
}
