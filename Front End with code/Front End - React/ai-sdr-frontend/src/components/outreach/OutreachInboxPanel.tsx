import { Inbox, Mail, RefreshCw, Reply, Send, Video } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { OutreachCampaign } from '../../api/types'
import {
  EmptyState,
  FilterBar,
  InlineBanner,
  ListLoading,
  WsSearchInput,
} from '../workspace'
import { OutreachCampaignDetailPanel, type PendingAction } from './OutreachCampaignDetailPanel'
import { OutreachCampaignRow, campaignKey } from './OutreachCampaignRow'
import { OUTREACH_FILTERS, formatCount, performanceMetrics } from './outreachUtils'

type OutreachInboxPanelProps = {
  campaigns: OutreachCampaign[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  statusFilter: string
  onStatusFilterChange: (value: string) => void
  onRetry: () => void
  performance?: Record<string, unknown>
  onRequestAction: (pending: PendingAction) => void
  onPause: (id: string) => void
  onResume: (id: string) => void
  onCancel: (id: string) => void
  actionPending: boolean
  onCreate: () => void
  createPending: boolean
}

export function OutreachInboxPanel({
  campaigns,
  isLoading,
  isFetching,
  error,
  statusFilter,
  onStatusFilterChange,
  onRetry,
  performance,
  onRequestAction,
  onPause,
  onResume,
  onCancel,
  actionPending,
  onCreate,
  createPending,
}: OutreachInboxPanelProps) {
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const filterOptions = OUTREACH_FILTERS.map((option) => ({
    ...option,
    count: campaigns.filter((c) => String(c.status) === option.id).length,
  }))

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return campaigns.filter((campaign) => {
      if (!q) return true
      return [campaign.contact_name, campaign.campaign_id, campaign.subject, campaign.status]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
        .includes(q)
    })
  }, [campaigns, query])

  const selected =
    filtered.find((campaign) => campaignKey(campaign) === selectedId) ?? filtered[0] ?? null

  const selectedKey = selected ? campaignKey(selected) : null

  const perf = performanceMetrics(performance)
  const kpis = [
    { label: 'Campaigns', value: formatCount(campaigns.length), hint: 'In current filter', icon: Inbox },
    { label: 'Sent', value: formatCount(perf[0]?.value ?? 0), hint: 'Total messages sent', icon: Send },
    { label: 'Replied', value: formatCount(perf[2]?.value ?? 0), hint: 'Inbound replies', icon: Reply },
    { label: 'Meetings', value: formatCount(perf[3]?.value ?? 0), hint: 'Booked meetings', icon: Video },
  ]

  return (
    <section className="sdr-outreach__inbox">
      <header className="sdr-outreach__inbox-header">
        <div>
          <p className="ws-heading-section">Inbox</p>
          <h2 className="sdr-outreach__pane-title">Campaign queue</h2>
          <p className="sdr-outreach__pane-desc">Approve, send, and monitor outbound sequences by status.</p>
        </div>
        <button type="button" className="ws-btn ws-btn--secondary ws-btn--compact" disabled={isFetching} onClick={onRetry}>
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
          Refresh
        </button>
      </header>

      <div className="sdr-outreach__kpi-row">
        {kpis.map((kpi) => (
          <article key={kpi.label} className="sdr-outreach-kpi">
            <span className="sdr-outreach-kpi__icon" aria-hidden>
              <kpi.icon className="h-4 w-4" />
            </span>
            <p className="ws-kpi-label">{kpi.label}</p>
            <p className="ws-kpi-value">{kpi.value}</p>
            <p className="ws-kpi-hint">{kpi.hint}</p>
          </article>
        ))}
      </div>

      <div className="sdr-outreach__filters">
        <WsSearchInput value={query} onChange={setQuery} placeholder="Search campaigns…" aria-label="Search campaigns" />
        <FilterBar options={filterOptions} activeId={statusFilter} onChange={onStatusFilterChange} aria-label="Campaign status" />
      </div>

      <div className="sdr-outreach__inbox-split">
        <div className="sdr-outreach__inbox-list-wrap">
          {error ? <InlineBanner message="Failed to load campaigns" onRetry={onRetry} /> : null}

          {isLoading ? (
            <ListLoading rows={5} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<Mail className="h-7 w-7" aria-hidden />}
              title={query ? 'No matching campaigns' : 'No campaigns'}
              description={
                query
                  ? 'Try a different search term.'
                  : 'Create a campaign from the compose panel or run the pipeline.'
              }
              action={
                !query ? (
                  <button type="button" className="ws-btn ws-btn--primary" disabled={createPending} onClick={onCreate}>
                    Create campaign
                  </button>
                ) : null
              }
            />
          ) : (
            <div className="sdr-outreach-result-list">
              {filtered.map((campaign) => {
                const key = campaignKey(campaign)
                return (
                  <OutreachCampaignRow
                    key={key}
                    campaign={campaign}
                    selected={selectedKey === key}
                    onSelect={() => setSelectedId(key)}
                  />
                )
              })}
            </div>
          )}
        </div>

        {selected ? (
          <OutreachCampaignDetailPanel
            campaign={selected}
            onRequestAction={onRequestAction}
            onPause={onPause}
            onResume={onResume}
            onCancel={onCancel}
            actionPending={actionPending}
          />
        ) : (
          <aside className="sdr-outreach__detail sdr-outreach__detail--empty hidden xl:flex">
            <div className="sdr-outreach__detail-placeholder">
              <Mail className="h-8 w-8" aria-hidden />
              <p>Select a campaign to review copy and take action.</p>
            </div>
          </aside>
        )}
      </div>
    </section>
  )
}
