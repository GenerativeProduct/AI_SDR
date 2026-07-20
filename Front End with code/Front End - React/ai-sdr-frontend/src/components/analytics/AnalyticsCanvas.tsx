import { useQuery } from '@tanstack/react-query'
import { Download, RefreshCw } from 'lucide-react'
import { api } from '../../api/client'
import { useDashboard } from '../../api/hooks'
import type {
  MeetingBooking,
  OutreachCampaign,
  ProspectIntelligenceResult,
  QualificationResult,
} from '../../api/types'
import { FunnelChart } from '../ui/FunnelChart'
import { FunnelSkeleton, TableSkeleton } from '../workspace/loading'

import { buildAnalyticsRows, exportAnalyticsCsv } from './analyticsUtils'

export function AnalyticsCanvas() {
  const dashboard = useDashboard()

  const intelligence = useQuery({
    queryKey: ['analytics-intelligence'],
    queryFn: () => api.get<ProspectIntelligenceResult[]>('/prospect-intelligence'),
  })
  const qualification = useQuery({
    queryKey: ['analytics-qualification'],
    queryFn: () => api.get<QualificationResult[]>('/qualification'),
  })
  const campaigns = useQuery({
    queryKey: ['analytics-campaigns'],
    queryFn: () => api.get<{ items: OutreachCampaign[]; total: number }>('/outreach/campaigns'),
  })
  const meetings = useQuery({
    queryKey: ['analytics-meetings'],
    queryFn: () => api.get<{ items: MeetingBooking[]; total: number }>('/meetings'),
  })

  const d = dashboard.data
  const funnelStages = [
    { label: 'ICPs defined', value: d?.icp_count ?? 0 },
    { label: 'Accounts discovered', value: d?.accounts_count ?? 0 },
    { label: 'Contacts found', value: d?.contacts_count ?? 0 },
    { label: 'Enriched', value: d?.enrichments_count ?? 0 },
    { label: 'Intelligence scored', value: d?.intelligence_count ?? 0 },
    { label: 'SQL / MQL qualified', value: d?.qualified_sql_mql ?? 0 },
    { label: 'Pending campaigns', value: d?.pending_campaigns ?? 0 },
    { label: 'Active conversations', value: d?.active_conversations ?? 0 },
    { label: 'Upcoming meetings', value: d?.upcoming_meetings ?? 0 },
  ]

  const intelItems = Array.isArray(intelligence.data) ? intelligence.data : []
  const qualItems = Array.isArray(qualification.data) ? qualification.data : []

  const rows = buildAnalyticsRows({
    intelligence: intelItems,
    qualification: qualItems,
    campaigns: campaigns.data?.items ?? [],
    meetings: meetings.data?.items ?? [],
  })

  const tableLoading =
    intelligence.isLoading || qualification.isLoading || campaigns.isLoading || meetings.isLoading

  return (
    <section className="sdr-split__right">
      <header className="sdr-split__right-header">
        <div>
          <p className="ws-heading-section">Reporting</p>
          <h2 className="sdr-split__pane-title">Pipeline analytics</h2>
          <p className="sdr-split__pane-desc">Cross-module funnel and record-level export.</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="ws-btn ws-btn--secondary ws-btn--compact"
            onClick={() => dashboard.refetch()}
          >
            <RefreshCw className={`h-4 w-4 ${dashboard.isFetching ? 'animate-spin' : ''}`} aria-hidden />
            Refresh
          </button>
          <button type="button" className="ws-btn ws-btn--primary ws-btn--compact" onClick={() => exportAnalyticsCsv(rows)}>
            <Download className="h-4 w-4" aria-hidden />
            Export CSV
          </button>
        </div>
      </header>

      <div className="sdr-split__canvas-scroll">
        <article className="sdr-split__canvas-card">
          <h3 className="sdr-split__canvas-card__title">Pipeline funnel</h3>
          <div className="mt-4">
            {dashboard.isLoading ? <FunnelSkeleton rows={9} /> : <FunnelChart stages={funnelStages} />}
          </div>
        </article>

        <article className="sdr-split__canvas-card">
          <h3 className="sdr-split__canvas-card__title">Cross-module records</h3>
          <div className="mt-4">
            {tableLoading ? (
              <TableSkeleton rows={6} cols={3} />
            ) : (
              <div className="sdr-split__table-wrap">
                <table className="sdr-split__table">
                  <thead>
                    <tr>
                      <th>Stage</th>
                      <th>Contact</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={`${r.stage}-${r.contact_id ?? r.campaign_id ?? r.meeting_id ?? i}`}>
                        <td className="capitalize">{String(r.stage)}</td>
                        <td>{String(r.contact_name ?? '—')}</td>
                        <td>{String(r.status ?? '—')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </article>
      </div>
    </section>
  )
}

export type { AnalyticsRow } from './analyticsUtils'
