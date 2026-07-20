import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Calendar, Mail, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { useConversationAgentStatus, useConversations } from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import { ConversationInboxPanel } from '../components/conversations/ConversationInboxPanel'
import { ConversationToolsPanel } from '../components/conversations/ConversationToolsPanel'
import type { PendingAction } from '../components/conversations/ConversationDetailPanel'
import { PageHeader, WorkspaceConfirmModal } from '../components/workspace'
import { pageTitles } from '../config/navigation'
import { useState } from 'react'

export function ConversationsPage() {
  const qc = useQueryClient()
  const [pending, setPending] = useState<PendingAction | null>(null)

  const threads = useConversations()
  const agentStatus = useConversationAgentStatus()

  const approveReply = useMutation({
    mutationFn: (id: string) =>
      api.post(`/conversations/${id}/approve-reply`, { approved_by: 'frontend-user' }),
    onSuccess: () => {
      toast.success('Reply approved')
      qc.invalidateQueries({ queryKey: queryKeys.conversations.list() })
      setPending(null)
    },
  })

  const sendReply = useMutation({
    mutationFn: (id: string) => api.post(`/conversations/${id}/send-reply`),
    onSuccess: () => {
      toast.success('Reply sent')
      qc.invalidateQueries({ queryKey: queryKeys.conversations.list() })
      setPending(null)
    },
  })

  const items = threads.data?.items ?? []
  const actionPending = approveReply.isPending || sendReply.isPending

  return (
    <section className="sdr-split sdr-conversations">
      <WorkspaceConfirmModal
        open={Boolean(pending)}
        title={pending?.action === 'send' ? 'Send reply?' : 'Approve reply?'}
        message="This action requires operator approval."
        confirmLabel={pending?.action === 'send' ? 'Send' : 'Approve'}
        onConfirm={() => {
          if (!pending) return
          if (pending.action === 'approve') approveReply.mutate(pending.id)
          else sendReply.mutate(pending.id)
        }}
        onCancel={() => setPending(null)}
        loading={actionPending}
      />

      <PageHeader
        embedded
        flush
        className="sdr-split__header"
        eyebrow="Operations"
        title={pageTitles['/conversations'] ?? 'Conversations'}
        description="Inbound replies and drafted responses — approve before send."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={threads.isFetching}
              onClick={() => threads.refetch()}
            >
              <RefreshCw className={`h-4 w-4 ${threads.isFetching ? 'animate-spin' : ''}`} aria-hidden />
              Refresh
            </button>
            <Link to="/outreach" className="ws-btn ws-btn--secondary">
              <Mail className="h-4 w-4" aria-hidden />
              Outreach
            </Link>
            <Link to="/meetings" className="ws-btn ws-btn--primary">
              <Calendar className="h-4 w-4" aria-hidden />
              Meetings
            </Link>
          </>
        }
      />

      <div className="sdr-split__workspace">
        <ConversationToolsPanel agentStatus={String(agentStatus.data?.status ?? '')} />
        <ConversationInboxPanel
          threads={items}
          isLoading={threads.isLoading}
          isFetching={threads.isFetching}
          error={threads.error}
          onRetry={() => threads.refetch()}
          onRequestAction={setPending}
          actionPending={actionPending}
        />
      </div>
    </section>
  )
}
