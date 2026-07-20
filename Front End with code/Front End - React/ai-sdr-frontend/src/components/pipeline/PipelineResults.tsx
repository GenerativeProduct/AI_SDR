import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { api } from '../../api/client'
import { queryKeys } from '../../api/queryKeys'
import type { SDRPipelineResponse } from '../../api/types'
import { RoleGuard } from '../auth/RoleGuard'
import {
  KpiMetric,
  KpiMetricGrid,
  StageAccordion,
  StatusBadge,
  WorkspaceConfirmModal,
} from '../workspace'

type PendingAction =
  | { type: 'approve-campaign'; id: string; label: string }
  | { type: 'send-campaign'; id: string; label: string }

export function PipelineResults({ result, embedded = false }: { result: SDRPipelineResponse; embedded?: boolean }) {
  const qc = useQueryClient()
  const [pending, setPending] = useState<PendingAction | null>(null)

  const summary = result.summary ?? {}
  const icp = result.icp_definition as Record<string, unknown>
  const accountCriteria = (icp.account_criteria ?? {}) as Record<string, unknown>
  const personaCriteria = (icp.persona_criteria ?? {}) as Record<string, unknown>

  const approveCampaign = useMutation({
    mutationFn: (id: string) =>
      api.post(`/outreach/campaigns/${id}/approve`, { approved_by: 'frontend-user' }),
    onSuccess: () => {
      toast.success('Campaign approved')
      qc.invalidateQueries({ queryKey: queryKeys.outreach.campaigns() })
      setPending(null)
    },
  })

  const sendCampaign = useMutation({
    mutationFn: (id: string) => api.post(`/outreach/campaigns/${id}/send`),
    onSuccess: () => {
      toast.success('Campaign sent')
      qc.invalidateQueries({ queryKey: queryKeys.outreach.campaigns() })
      setPending(null)
    },
  })

  const handleConfirm = () => {
    if (!pending) return
    if (pending.type === 'approve-campaign') approveCampaign.mutate(pending.id)
    if (pending.type === 'send-campaign') sendCampaign.mutate(pending.id)
  }

  return (
    <div className={embedded ? 'sdr-pipeline__results' : 'ws-page-body'}>
      <WorkspaceConfirmModal
        open={Boolean(pending)}
        title={pending?.type === 'send-campaign' ? 'Send campaign?' : 'Approve campaign?'}
        message={
          pending
            ? `Confirm action for ${pending.label}. This will be recorded in the audit trail.`
            : ''
        }
        confirmLabel={pending?.type === 'send-campaign' ? 'Send' : 'Approve'}
        onConfirm={handleConfirm}
        onCancel={() => setPending(null)}
        loading={approveCampaign.isPending || sendCampaign.isPending}
      />

      <KpiMetricGrid columns={6}>
        <KpiMetric label="Accounts" value={summary.accounts_discovered ?? 0} />
        <KpiMetric label="Contacts" value={summary.contacts_discovered ?? 0} />
        <KpiMetric label="Enriched" value={summary.accounts_enriched ?? 0} />
        <KpiMetric label="Analyzed" value={summary.prospects_analyzed ?? 0} />
        <KpiMetric label="Campaigns" value={summary.campaigns_drafted ?? 0} />
        <KpiMetric label="Follow-ups" value={summary.follow_up_plans_drafted ?? 0} />
      </KpiMetricGrid>

      {(summary.accounts_discovered ?? 0) > 0 && (summary.contacts_discovered ?? 0) === 0 ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Accounts were discovered but no contacts were returned. Check discovery settings in{' '}
          <Link to="/settings" className="font-medium underline">
            Settings
          </Link>
          .
        </div>
      ) : null}

      {result.warnings?.length ? (
        <div className="ws-card text-sm text-[var(--ws-text-secondary)]">
          <p className="font-medium text-[var(--ws-text-primary)]">Warnings</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {result.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <StageAccordion title="1. ICP setup" defaultOpen>
        <ul className="space-y-1">
          <li>Industries: {(accountCriteria.industries as string[])?.join(', ') || '—'}</li>
          <li>Geographies: {(accountCriteria.geographies as string[])?.join(', ') || '—'}</li>
          <li>Personas: {(personaCriteria.titles as string[])?.join(', ') || '—'}</li>
        </ul>
      </StageAccordion>

      <StageAccordion title="2. Prospect discovery" defaultOpen>
        <p className="mb-2">
          {result.discovered_accounts?.length ?? 0} accounts,{' '}
          {result.discovered_contacts?.length ?? 0} contacts
        </p>
        <ul className="space-y-1">
          {result.discovered_accounts?.slice(0, 5).map((a) => (
            <li key={String(a.account_id)}>
              {String(a.company_name)} — fit {String(a.fit_score ?? 'n/a')}
            </li>
          ))}
        </ul>
      </StageAccordion>

      <StageAccordion title="3. Enrichment">
        {result.enriched_results?.length ? (
          result.enriched_results.map((e, i) => (
            <div key={i} className="mb-3 border-b border-[var(--ws-border)] pb-3 last:border-0">
              <p className="font-medium text-[var(--ws-text-primary)]">
                {String(e.company_name ?? e.account_id)}
              </p>
              <p className="text-[var(--ws-text-muted)]">{String(e.company_summary ?? '')}</p>
            </div>
          ))
        ) : (
          <p>No enrichment results</p>
        )}
      </StageAccordion>

      <StageAccordion title="3b. Intelligence scores">
        <ul className="space-y-1">
          {result.prospect_intelligence?.map((p) => (
            <li key={p.intelligence_id ?? p.contact_id}>
              {p.contact_name} — intent {p.intent?.level ?? 'n/a'}
            </li>
          ))}
        </ul>
      </StageAccordion>

      <StageAccordion title="4. Qualification">
        <ul className="space-y-1">
          {result.qualification_results?.map((q) => (
            <li key={String(q.qualification_id ?? q.contact_id)}>
              {String(q.contact_name)} — {String(q.qualification_status)}
            </li>
          ))}
        </ul>
      </StageAccordion>

      <StageAccordion title="5. Outreach">
        <ul className="space-y-3">
          {result.outreach_campaigns?.map((c) => (
            <li
              key={String(c.campaign_id)}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--ws-border)] px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <span className="text-[var(--ws-text-primary)]">
                  {String(c.contact_name ?? c.campaign_id)}
                </span>
                <StatusBadge status={String(c.status)} />
              </div>
              <RoleGuard requireApprove>
                <div className="flex gap-2">
                  {c.status === 'pending_approval' ? (
                    <button
                      type="button"
                      className="ws-btn ws-btn--secondary ws-btn--compact"
                      onClick={() =>
                        setPending({
                          type: 'approve-campaign',
                          id: String(c.campaign_id),
                          label: String(c.contact_name ?? c.campaign_id),
                        })
                      }
                    >
                      Approve
                    </button>
                  ) : null}
                  {['approved', 'active', 'running'].includes(String(c.status)) ? (
                    <button
                      type="button"
                      className="ws-btn ws-btn--primary ws-btn--compact"
                      onClick={() =>
                        setPending({
                          type: 'send-campaign',
                          id: String(c.campaign_id),
                          label: String(c.contact_name ?? c.campaign_id),
                        })
                      }
                    >
                      Send
                    </button>
                  ) : null}
                </div>
              </RoleGuard>
            </li>
          ))}
        </ul>
      </StageAccordion>

      <StageAccordion title="5b. Follow-up">
        <ul className="space-y-1">
          {result.follow_up_plans?.map((p) => (
            <li key={String(p.plan_id)}>
              Plan {String(p.plan_id)} — {String(p.status)}
            </li>
          ))}
        </ul>
      </StageAccordion>

      {(result.outreach_campaigns?.length ?? 0) > 0 ? (
        <StageAccordion title="6. Next steps">
          <p className="text-sm text-[var(--ws-text-muted)]">
            After sending campaigns, monitor replies and book meetings from the ops console.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link to="/conversations" className="ws-btn ws-btn--secondary ws-btn--compact">
              Conversations
            </Link>
            <Link to="/meetings" className="ws-btn ws-btn--primary ws-btn--compact">
              Meetings & CRM
            </Link>
          </div>
        </StageAccordion>
      ) : null}
    </div>
  )
}
