import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, MessageSquare, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { useCampaigns, useFollowUpPlans, useFollowUpSchedulerStatus } from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import type { FollowUpPlan } from '../api/types'
import { FollowUpComposePanel } from '../components/follow-up/FollowUpComposePanel'
import { FollowUpPlansPanel } from '../components/follow-up/FollowUpPlansPanel'
import { PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function FollowUpPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const [campaignId, setCampaignId] = useState('')
  const [contactId, setContactId] = useState('')
  const qc = useQueryClient()

  const plans = useFollowUpPlans(statusFilter || undefined)
  const scheduler = useFollowUpSchedulerStatus()
  const campaigns = useCampaigns()

  const createPlan = useMutation({
    mutationFn: () =>
      api.post('/follow-up/plans', {
        campaign_id: campaignId,
        contact_id: contactId,
        require_approval: true,
      }),
    onSuccess: () => {
      toast.success('Plan created')
      qc.invalidateQueries({ queryKey: queryKeys.followUp.plans() })
    },
    onError: () => toast.error('Create failed'),
  })

  const approvePlan = useMutation({
    mutationFn: (plan: FollowUpPlan) =>
      api.post(`/follow-up/plans/${plan.plan_id}/approve`, { approved_by: 'frontend-user' }),
    onSuccess: () => {
      toast.success('Plan approved')
      qc.invalidateQueries({ queryKey: queryKeys.followUp.plans() })
    },
    onError: () => toast.error('Approve failed'),
  })

  const campaignOptions =
    campaigns.data?.items?.map((c) => ({
      value: c.campaign_id,
      label: String(c.contact_name ?? c.campaign_id),
    })) ?? []

  const items = plans.data?.items ?? []

  return (
    <section className="sdr-split sdr-follow-up">
      <PageHeader
        embedded
        flush
        className="sdr-split__header"
        eyebrow="Operations"
        title={pageTitles['/follow-up'] ?? 'Follow-Up'}
        description="Multi-touch sequences after outreach — approve before activation."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={plans.isFetching}
              onClick={() => plans.refetch()}
            >
              <RefreshCw className={`h-4 w-4 ${plans.isFetching ? 'animate-spin' : ''}`} aria-hidden />
              Refresh
            </button>
            <Link to="/outreach" className="ws-btn ws-btn--secondary">
              <Mail className="h-4 w-4" aria-hidden />
              Outreach
            </Link>
            <Link to="/conversations" className="ws-btn ws-btn--primary">
              <MessageSquare className="h-4 w-4" aria-hidden />
              Conversations
            </Link>
          </>
        }
      />

      <div className="sdr-split__workspace">
        <FollowUpComposePanel
          campaignId={campaignId}
          contactId={contactId}
          campaignOptions={campaignOptions}
          schedulerBackend={String(scheduler.data?.scheduler_backend ?? '')}
          onCampaignChange={setCampaignId}
          onContactChange={setContactId}
          onCreate={() => createPlan.mutate()}
          createPending={createPlan.isPending}
        />

        <FollowUpPlansPanel
          plans={items}
          isLoading={plans.isLoading}
          isFetching={plans.isFetching}
          error={plans.error}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          onRetry={() => plans.refetch()}
          onApprove={(plan) => approvePlan.mutate(plan)}
          approvePending={approvePlan.isPending}
          onCreate={() => createPlan.mutate()}
          createPending={createPlan.isPending}
        />
      </div>
    </section>
  )
}
