import {
  useDashboard,
  useDiscoveryStatus,
  useEnrichmentStatus,
  useMeetingsStatus,
} from '../api/hooks'
import {
  Activity,
  CalendarClock,
  Mail,
  RefreshCw,
  Target,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { pageTitles } from '../config/navigation'
import { PipelineAnalyticsPanel } from '../components/dashboard/PipelineAnalyticsPanel'
import {
  DashboardHealthPanel,
  healthRevenueIcons,
} from '../components/dashboard/DashboardHealthPanel'
import { DashboardKpiCard } from '../components/dashboard/DashboardKpiCard'
import { PageHeader } from '../components/workspace/PageHeader'

export function DashboardPage() {
  const { data, isLoading, error, refetch, isFetching } = useDashboard()
  const enrichmentStatus = useEnrichmentStatus()
  const discoveryStatus = useDiscoveryStatus()
  const meetingStatus = useMeetingsStatus()

  const funnelStages = [
    { label: 'ICPs', value: data?.icp_count ?? 0 },
    { label: 'Accounts', value: data?.accounts_count ?? 0 },
    { label: 'Contacts', value: data?.contacts_count ?? 0 },
    { label: 'Enriched', value: data?.enrichments_count ?? 0 },
    { label: 'Intelligence', value: data?.intelligence_count ?? 0 },
    { label: 'SQL / MQL', value: data?.qualified_sql_mql ?? 0 },
    { label: 'Campaigns', value: data?.pending_campaigns ?? 0 },
    { label: 'Conversations', value: data?.active_conversations ?? 0 },
    { label: 'Meetings', value: data?.upcoming_meetings ?? 0 },
  ]

  const stageBars = [
    { label: 'ICP', value: data?.icp_count ?? 0 },
    { label: 'Discovery', value: data?.accounts_count ?? 0 },
    { label: 'Enrich', value: data?.enrichments_count ?? 0 },
    { label: 'Intel', value: data?.intelligence_count ?? 0 },
    { label: 'Qualify', value: data?.qualified_sql_mql ?? 0 },
    { label: 'Outreach', value: data?.pending_campaigns ?? 0 },
  ]

  const pipelineTotal =
    (data?.accounts_count ?? 0) +
    (data?.contacts_count ?? 0) +
    (data?.enrichments_count ?? 0) +
    (data?.intelligence_count ?? 0)

  const crmFailures = data?.crm_sync_failures ?? 0
  const activeConversations = data?.active_conversations ?? 0

  const topKpis = [
    {
      label: 'Pipeline objects',
      value: pipelineTotal,
      hint: 'Accounts, contacts, enrichment, and intel',
      icon: Activity,
      to: '/pipeline',
    },
    {
      label: 'Upcoming meetings',
      value: data?.upcoming_meetings ?? 0,
      hint: 'Scheduled across connected calendars',
      icon: CalendarClock,
      to: '/meetings',
    },
    {
      label: 'CRM sync failures',
      value: crmFailures,
      hint: crmFailures > 0 ? 'Review failed sync jobs in CRM' : 'No failed sync jobs',
      icon: Target,
      tone: crmFailures > 0 ? ('risk' as const) : ('default' as const),
      badge: crmFailures > 0 ? 'Needs attention' : undefined,
      to: '/crm',
    },
    {
      label: 'Active conversations',
      value: activeConversations,
      hint: activeConversations > 0 ? 'Replies awaiting follow-up' : 'No open reply threads',
      icon: Mail,
      tone: activeConversations > 0 ? ('success' as const) : ('default' as const),
      badge: activeConversations > 0 ? 'Live' : undefined,
      to: '/conversations',
    },
  ]

  const readiness = [
    {
      label: 'Discovery',
      ok: Boolean(discoveryStatus.data?.account_providers),
      detail: String(discoveryStatus.data?.contact_provider ?? 'Waiting for provider'),
    },
    {
      label: 'Enrichment',
      ok: Boolean(enrichmentStatus.data?.live_search_configured),
      detail: String(enrichmentStatus.data?.detail ?? 'Not configured'),
    },
    {
      label: 'Meetings',
      ok: Boolean(meetingStatus.data?.provider_configured),
      detail: String(meetingStatus.data?.provider ?? 'Not configured'),
    },
  ]

  const revenueOps = [
    {
      label: 'Pending campaigns',
      value: data?.pending_campaigns ?? 0,
      icon: healthRevenueIcons.campaigns,
    },
    {
      label: 'Upcoming meetings',
      value: data?.upcoming_meetings ?? 0,
      icon: healthRevenueIcons.meetings,
    },
    {
      label: 'CRM failures',
      value: crmFailures,
      icon: healthRevenueIcons.crm,
    },
    {
      label: 'Follow-up pending',
      value: data?.follow_up_plans_pending ?? 0,
      icon: healthRevenueIcons.followUp,
    },
  ]

  return (
    <section className="sdr-dashboard">
      <PageHeader
        embedded
        flush
        className="sdr-dashboard__header"
        eyebrow="Operations"
        title={pageTitles['/'] ?? 'SDR Dashboard'}
        description="Live pipeline funnel, module volume, and integration health in one operations view."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={isFetching}
              onClick={() => refetch()}
            >
              <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
              Refresh
            </button>
            <Link to="/analytics" className="ws-btn ws-btn--secondary">
              Full analytics
            </Link>
            <Link to="/pipeline" className="ws-btn ws-btn--primary">
              Open pipeline
            </Link>
          </>
        }
      />

      <div className="sdr-dashboard__body">
        {error ? (
          <div className="ws-banner ws-banner--error">
            Failed to load dashboard data. Retry refresh once the API is reachable.
          </div>
        ) : null}

        <div className="sdr-dashboard__kpi-row">
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="sdr-kpi-card sdr-kpi-card--skeleton" aria-busy>
                  <div className="ws-skeleton h-3 w-24 rounded" />
                  <div className="ws-skeleton mt-3 h-9 w-16 rounded" />
                  <div className="ws-skeleton mt-2 h-3 w-32 rounded" />
                </div>
              ))
            : topKpis.map((kpi) => <DashboardKpiCard key={kpi.label} {...kpi} />)}
        </div>

        <div className="sdr-dashboard__main-grid">
          <PipelineAnalyticsPanel
            funnelStages={funnelStages}
            stageBars={stageBars}
            isLoading={isLoading}
          />

          <aside className="sdr-dash-panel sdr-dash-panel--side">
            <header className="sdr-dash-panel__header">
              <p className="ws-heading-section">Health</p>
              <h2 className="sdr-dash-panel__title-lg">System readiness</h2>
              <p className="sdr-dash-panel__desc">Integration status, revenue pressure, and shortcuts.</p>
            </header>
            <DashboardHealthPanel readiness={readiness} revenue={revenueOps} />
          </aside>
        </div>
      </div>
    </section>
  )
}
