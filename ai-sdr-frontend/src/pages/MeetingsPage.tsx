import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MessageSquare, RefreshCw, Users } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { useConversations, useCrmSyncs, useMeetings } from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import { MeetingComposePanel } from '../components/meetings/MeetingComposePanel'
import { MeetingInboxPanel } from '../components/meetings/MeetingInboxPanel'
import { PageHeader, WorkspaceConfirmModal } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function MeetingsPage() {
  const qc = useQueryClient()
  const [bookDate, setBookDate] = useState('')
  const [bookTime, setBookTime] = useState('10:00')
  const [pendingBookId, setPendingBookId] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState('')

  const meetings = useMeetings()
  const crmSyncs = useCrmSyncs()
  const conversations = useConversations()

  const conversationOptions =
    conversations.data?.items?.map((c) => ({
      value: c.conversation_id,
      label: c.conversation_id,
    })) ?? []

  const createRequest = useMutation({
    mutationFn: () =>
      api.post('/meetings/requests', {
        conversation_id: conversationId,
        proposed_times: [],
      }),
    onSuccess: () => {
      toast.success('Meeting request created')
      qc.invalidateQueries({ queryKey: queryKeys.meetings.list() })
    },
    onError: () => toast.error('Request failed'),
  })

  const book = useMutation({
    mutationFn: (id: string) =>
      api.post(`/meetings/${id}/approve-and-book`, {
        approved_by: 'frontend-user',
        scheduled_at: `${bookDate}T${bookTime}:00Z`,
        duration_minutes: 30,
      }),
    onSuccess: () => {
      toast.success('Meeting booked')
      qc.invalidateQueries({ queryKey: queryKeys.meetings.list() })
      setPendingBookId(null)
    },
    onError: () => toast.error('Booking failed'),
  })

  const cancel = useMutation({
    mutationFn: (id: string) => api.post(`/meetings/${id}/cancel`, { reason: 'operator' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.meetings.list() }),
  })

  const retryCrm = useMutation({
    mutationFn: (id: string) => api.post(`/meetings/${id}/retry-crm`),
    onSuccess: () => {
      toast.success('Retrying CRM sync')
      qc.invalidateQueries({ queryKey: queryKeys.crm.syncs })
    },
  })

  const sendReminder = useMutation({
    mutationFn: ({ id, type }: { id: string; type: '24h' | '1h' }) =>
      api.post(`/meetings/${id}/reminders/${type}`),
    onSuccess: () => toast.success('Reminder queued'),
  })

  const syncRecords = Array.isArray(crmSyncs.data) ? crmSyncs.data : []
  const items = meetings.data?.items ?? []
  const actionPending =
    book.isPending || cancel.isPending || retryCrm.isPending || sendReminder.isPending

  const refreshAll = () => {
    meetings.refetch()
    crmSyncs.refetch()
    conversations.refetch()
  }

  return (
    <section className="sdr-split sdr-meetings">
      <WorkspaceConfirmModal
        open={Boolean(pendingBookId)}
        title="Approve and book meeting?"
        message={`Book for ${bookDate} at ${bookTime} UTC.`}
        confirmLabel="Book meeting"
        onConfirm={() => pendingBookId && book.mutate(pendingBookId)}
        onCancel={() => setPendingBookId(null)}
        loading={book.isPending}
      />

      <PageHeader
        embedded
        flush
        className="sdr-split__header"
        eyebrow="Operations"
        title={pageTitles['/meetings'] ?? 'Meetings & CRM'}
        description="Approve bookings, reminders, and CRM sync from conversation threads."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={meetings.isFetching}
              onClick={refreshAll}
            >
              <RefreshCw className={`h-4 w-4 ${meetings.isFetching ? 'animate-spin' : ''}`} aria-hidden />
              Refresh
            </button>
            <Link to="/conversations" className="ws-btn ws-btn--secondary">
              <MessageSquare className="h-4 w-4" aria-hidden />
              Conversations
            </Link>
            <Link to="/crm" className="ws-btn ws-btn--primary">
              <Users className="h-4 w-4" aria-hidden />
              CRM audit
            </Link>
          </>
        }
      />

      <div className="sdr-split__workspace">
        <MeetingComposePanel
          conversationId={conversationId}
          conversationOptions={conversationOptions}
          bookDate={bookDate}
          bookTime={bookTime}
          onConversationChange={setConversationId}
          onBookDateChange={setBookDate}
          onBookTimeChange={setBookTime}
          onCreateRequest={() => createRequest.mutate()}
          createPending={createRequest.isPending}
        />

        <MeetingInboxPanel
          meetings={items}
          crmSyncs={syncRecords}
          isLoading={meetings.isLoading}
          isFetching={meetings.isFetching}
          error={meetings.error}
          bookDate={bookDate}
          bookTime={bookTime}
          onRetry={refreshAll}
          onRequestBook={setPendingBookId}
          onRetryCrm={(id) => retryCrm.mutate(id)}
          onSendReminder={(id, type) => sendReminder.mutate({ id, type })}
          onCancel={(id) => cancel.mutate(id)}
          actionPending={actionPending}
          onCreateRequest={() => createRequest.mutate()}
          createPending={createRequest.isPending}
        />
      </div>
    </section>
  )
}
