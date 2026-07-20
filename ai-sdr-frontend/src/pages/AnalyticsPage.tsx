import { useQuery } from '@tanstack/react-query'
import { BarChart3, Database, Download, TrendingUp } from 'lucide-react'
import { api } from '../api/client'
import { useDashboard } from '../api/hooks'
import type {
  MeetingBooking,
  OutreachCampaign,
  ProspectIntelligenceResult,
  QualificationResult,
} from '../api/types'
import { AnalyticsCanvas } from '../components/analytics/AnalyticsCanvas'
import { buildAnalyticsRows, exportAnalyticsCsv } from '../components/analytics/analyticsUtils'
import { PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function AnalyticsPage() {
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

  const exportCsv = () => {
    const rows = buildAnalyticsRows({
      intelligence: Array.isArray(intelligence.data) ? intelligence.data : [],
      qualification: Array.isArray(qualification.data) ? qualification.data : [],
      campaigns: campaigns.data?.items ?? [],
      meetings: meetings.data?.items ?? [],
    })
    exportAnalyticsCsv(rows)
  }

  const kpis = [
    { label: 'Accounts', value: String(d?.accounts_count ?? 0), icon: Database },
    { label: 'Qualified', value: String(d?.qualified_sql_mql ?? 0), icon: TrendingUp },
    { label: 'Campaigns', value: String(d?.pending_campaigns ?? 0), icon: BarChart3 },
    { label: 'Meetings', value: String(d?.upcoming_meetings ?? 0), icon: Download },
  ]

  return (
    <section className="sdr-split sdr-analytics">
      <PageHeader
        embedded
        flush
        className="sdr-split__header"
        eyebrow="Insights"
        title={pageTitles['/analytics'] ?? 'Analytics'}
        description="Cross-module SDR reporting — funnel conversion and record-level export."
        actions={
          <button type="button" className="ws-btn ws-btn--primary" onClick={exportCsv}>
            <Download className="h-4 w-4" aria-hidden />
            Export CSV
          </button>
        }
      />

      <div className="sdr-split__workspace">
        <aside className="sdr-split__left">
          <header className="sdr-split__left-header">
            <div>
              <p className="ws-heading-section">Summary</p>
              <h2 className="sdr-split__pane-title">Key metrics</h2>
              <p className="sdr-split__pane-desc">Live counts from the dashboard API.</p>
            </div>
          </header>
          <div className="sdr-split__left-body">
            <div className="grid gap-2">
              {kpis.map((kpi) => (
                <article key={kpi.label} className="sdr-split-kpi">
                  <span className="sdr-split-kpi__icon" aria-hidden>
                    <kpi.icon className="h-4 w-4" />
                  </span>
                  <p className="ws-kpi-label">{kpi.label}</p>
                  <p className="ws-kpi-value">{kpi.value}</p>
                </article>
              ))}
            </div>
            <div className="sdr-split__meta-card">
              <p className="sdr-split__meta-card__label">Pipeline health</p>
              <dl className="sdr-split__meta-dl">
                <div>
                  <dt>ICPs</dt>
                  <dd>{d?.icp_count ?? 0}</dd>
                </div>
                <div>
                  <dt>Contacts</dt>
                  <dd>{d?.contacts_count ?? 0}</dd>
                </div>
                <div>
                  <dt>Conversations</dt>
                  <dd>{d?.active_conversations ?? 0}</dd>
                </div>
              </dl>
            </div>
          </div>
        </aside>

        <AnalyticsCanvas />
      </div>
    </section>
  )
}
