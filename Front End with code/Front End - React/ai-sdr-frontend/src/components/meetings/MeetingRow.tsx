import { Calendar } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { MeetingBooking } from '../../api/types'
import { StatusBadge } from '../workspace'
import { formatDate } from '../../lib/utils'

type MeetingRowProps = {
  meeting: MeetingBooking
  selected: boolean
  onSelect: () => void
}

export function MeetingRow({ meeting, selected, onSelect }: MeetingRowProps) {
  return (
    <button
      type="button"
      className={cn('sdr-split-row ws-focus-ring', selected && 'sdr-split-row--active')}
      onClick={onSelect}
    >
      <span className="sdr-split-row__icon" aria-hidden>
        <Calendar className="h-4 w-4" />
      </span>
      <span className="sdr-split-row__copy">
        <span className="sdr-split-row__head">
          <span className="sdr-split-row__name">{meeting.contact_name ?? meeting.meeting_id}</span>
          <StatusBadge status={String(meeting.status)} />
        </span>
        <span className="sdr-split-row__meta">{formatDate(meeting.scheduled_at)}</span>
      </span>
    </button>
  )
}
