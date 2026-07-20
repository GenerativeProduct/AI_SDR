import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FlaskConical, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { useCampaigns, useDiscoveredContacts, useOutreachPerformance } from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import { OutreachComposePanel } from '../components/outreach/OutreachComposePanel'
import { OutreachInboxPanel } from '../components/outreach/OutreachInboxPanel'
import type { PendingAction } from '../components/outreach/OutreachCampaignDetailPanel'
import { PageHeader, WorkspaceConfirmModal } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function OutreachPage() {
  const [statusFilter, setStatusFilter] = useState('pending_approval')
  const [pending, setPending] = useState<PendingAction | null>(null)
  const [contactId, setContactId] = useState('')
  const [channel, setChannel] = useState('email')
  const qc = useQueryClient()

  const campaigns = useCampaigns(statusFilter)
  const performance = useOutreachPerformance()
  const contacts = useDiscoveredContacts()

  const contactOptions = useMemo(
    () =>
      (contacts.data ?? []).map((contact) => ({
        value: contact.contact_id,
        label: `${contact.full_name} — ${contact.title}`,
      })),
    [contacts.data],
  )

  const selectedContact = (contacts.data ?? []).find((contact) => contact.contact_id === contactId)

  const createCampaign = useMutation({
    mutationFn: async () => {
      const contact = (contacts.data ?? []).find((item) => item.contact_id === contactId)
      return api.post('/outreach/campaigns', {
        contact,
        channel,
        require_approval: true,
        cadence: { touches: 3, spacing_hours: 48 },
      })
    },
    onSuccess: () => {
      toast.success('Campaign created')
      qc.invalidateQueries({ queryKey: queryKeys.outreach.campaigns() })
    },
    onError: () => toast.error('Create failed'),
  })

  const approve = useMutation({
    mutationFn: (id: string) =>
      api.post(`/outreach/campaigns/${id}/approve`, { approved_by: 'frontend-user' }),
    onSuccess: () => {
      toast.success('Campaign approved')
      qc.invalidateQueries({ queryKey: queryKeys.outreach.campaigns() })
      setPending(null)
    },
  })

  const send = useMutation({
    mutationFn: (id: string) => api.post(`/outreach/campaigns/${id}/send`),
    onSuccess: () => {
      toast.success('Campaign sent')
      qc.invalidateQueries({ queryKey: queryKeys.outreach.campaigns() })
      setPending(null)
    },
  })

  const pause = useMutation({
    mutationFn: (id: string) => api.post(`/outreach/campaigns/${id}/pause`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.outreach.campaigns() }),
  })

  const resume = useMutation({
    mutationFn: (id: string) => api.post(`/outreach/campaigns/${id}/resume`),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.outreach.campaigns() }),
  })

  const cancel = useMutation({
    mutationFn: (id: string) => api.post(`/outreach/campaigns/${id}/cancel`),
    onSuccess: () => {
      toast.success('Campaign canceled')
      qc.invalidateQueries({ queryKey: queryKeys.outreach.campaigns() })
    },
  })

  const runScheduler = useMutation({
    mutationFn: () => api.post('/outreach/scheduler/run-due'),
    onSuccess: () => toast.success('Scheduler ran'),
  })

  const items = campaigns.data?.items ?? []
  const actionPending =
    approve.isPending || send.isPending || pause.isPending || resume.isPending || cancel.isPending

  const refreshAll = () => {
    campaigns.refetch()
    performance.refetch()
    contacts.refetch()
  }

  return (
    <section className="sdr-outreach">
      <WorkspaceConfirmModal
        open={Boolean(pending)}
        title={pending?.action === 'send' ? 'Send campaign?' : 'Approve campaign?'}
        message={pending ? `Confirm for ${pending.label}.` : ''}
        confirmLabel={pending?.action === 'send' ? 'Send' : 'Approve'}
        onConfirm={() => {
          if (!pending) return
          if (pending.action === 'approve') approve.mutate(pending.id)
          else send.mutate(pending.id)
        }}
        onCancel={() => setPending(null)}
        loading={approve.isPending || send.isPending}
      />

      <PageHeader
        embedded
        flush
        className="sdr-outreach__header"
        eyebrow="Operations"
        title={pageTitles['/outreach'] ?? 'Outreach Inbox'}
        description="Review, approve, and send outbound campaigns — track opens, replies, and meetings."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={campaigns.isFetching}
              onClick={refreshAll}
            >
              <RefreshCw className={`h-4 w-4 ${campaigns.isFetching ? 'animate-spin' : ''}`} aria-hidden />
              Refresh
            </button>
            <Link to="/qualification" className="ws-btn ws-btn--secondary">
              <FlaskConical className="h-4 w-4" aria-hidden />
              Qualification
            </Link>
          </>
        }
      />

      <div className="sdr-outreach__workspace">
        <OutreachComposePanel
          contactId={contactId}
          channel={channel}
          contactOptions={contactOptions}
          selectedContact={selectedContact}
          onContactChange={setContactId}
          onChannelChange={setChannel}
          onCreate={() => createCampaign.mutate()}
          createPending={createCampaign.isPending}
          onRunScheduler={() => runScheduler.mutate()}
          schedulerPending={runScheduler.isPending}
        />

        <OutreachInboxPanel
          campaigns={items}
          isLoading={campaigns.isLoading}
          isFetching={campaigns.isFetching}
          error={campaigns.error}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          onRetry={() => campaigns.refetch()}
          performance={performance.data}
          onRequestAction={setPending}
          onPause={(id) => pause.mutate(id)}
          onResume={(id) => resume.mutate(id)}
          onCancel={(id) => cancel.mutate(id)}
          actionPending={actionPending}
          onCreate={() => createCampaign.mutate()}
          createPending={createCampaign.isPending}
        />
      </div>
    </section>
  )
}
