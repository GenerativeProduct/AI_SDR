import { MessageSquare } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { ConversationThread } from '../../api/types'
import { StatusBadge } from '../workspace'

type ConversationThreadRowProps = {
  thread: ConversationThread
  selected: boolean
  onSelect: () => void
}

export function ConversationThreadRow({ thread, selected, onSelect }: ConversationThreadRowProps) {
  return (
    <button
      type="button"
      className={cn('sdr-split-row ws-focus-ring', selected && 'sdr-split-row--active')}
      onClick={onSelect}
    >
      <span className="sdr-split-row__icon" aria-hidden>
        <MessageSquare className="h-4 w-4" />
      </span>
      <span className="sdr-split-row__copy">
        <span className="sdr-split-row__head">
          <span className="sdr-split-row__name">{thread.conversation_id}</span>
          <StatusBadge status={String(thread.status)} />
        </span>
        {thread.inbound_message ? (
          <span className="sdr-split-row__meta line-clamp-2">{String(thread.inbound_message)}</span>
        ) : null}
      </span>
    </button>
  )
}
