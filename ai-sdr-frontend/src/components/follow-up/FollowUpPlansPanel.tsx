import { Repeat, RefreshCw } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { FollowUpPlan } from '../../api/types'
import { EmptyState, FilterBar, InlineBanner, ListLoading, WsSearchInput } from '../workspace'
import { FollowUpDetailPanel } from './FollowUpDetailPanel'
import { FollowUpPlanRow } from './FollowUpPlanRow'
import { FOLLOW_UP_FILTERS, planKey } from './followUpUtils'

type FollowUpPlansPanelProps = {
  plans: FollowUpPlan[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  statusFilter: string
  onStatusFilterChange: (value: string) => void
  onRetry: () => void
  onApprove: (plan: FollowUpPlan) => void
  approvePending: boolean
  onCreate: () => void
  createPending: boolean
}

export function FollowUpPlansPanel({
  plans,
  isLoading,
  isFetching,
  error,
  statusFilter,
  onStatusFilterChange,
  onRetry,
  onApprove,
  approvePending,
  onCreate,
  createPending,
}: FollowUpPlansPanelProps) {
  const [query, setQuery] = useState('')
  const [selectedKey, setSelectedKey] = useState<string | null>(null)

  const filterOptions = FOLLOW_UP_FILTERS.map((option) => ({
    ...option,
    count: option.id === '' ? plans.length : plans.filter((p) => p.status === option.id).length,
  }))

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return plans.filter((plan) => {
      if (statusFilter && plan.status !== statusFilter) return false
      if (!q) return true
      return [plan.campaign_id, plan.contact_id, plan.status].join(' ').toLowerCase().includes(q)
    })
  }, [plans, query, statusFilter])

  const selected = filtered.find((p) => planKey(p) === selectedKey) ?? filtered[0] ?? null

  return (
    <section className="sdr-split__right">
      <header className="sdr-split__right-header">
        <div>
          <p className="ws-heading-section">Plans</p>
          <h2 className="sdr-split__pane-title">Follow-up queue</h2>
          <p className="sdr-split__pane-desc">Review multi-touch sequences and approve before activation.</p>
        </div>
        <button type="button" className="ws-btn ws-btn--secondary ws-btn--compact" disabled={isFetching} onClick={onRetry}>
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
          Refresh
        </button>
      </header>

      <div className="sdr-split__filters">
        <WsSearchInput value={query} onChange={setQuery} placeholder="Search plans…" aria-label="Search follow-up plans" />
        <FilterBar options={filterOptions} activeId={statusFilter} onChange={onStatusFilterChange} aria-label="Plan status" />
      </div>

      <div className="sdr-split__master-detail">
        <div className="sdr-split__list-wrap">
          {error ? <InlineBanner message="Failed to load plans" onRetry={onRetry} /> : null}

          {isLoading ? (
            <ListLoading rows={4} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<Repeat className="h-7 w-7" aria-hidden />}
              title={query || statusFilter ? 'No matching plans' : 'No follow-up plans'}
              description="Create a plan from a campaign."
              action={
                !query && !statusFilter ? (
                  <button type="button" className="ws-btn ws-btn--primary" disabled={createPending} onClick={onCreate}>
                    Create plan
                  </button>
                ) : null
              }
            />
          ) : (
            <div className="sdr-split-row-list">
              {filtered.map((plan) => {
                const key = planKey(plan)
                return (
                  <FollowUpPlanRow
                    key={key}
                    plan={plan}
                    selected={selected ? planKey(selected) === key : false}
                    onSelect={() => setSelectedKey(key)}
                  />
                )
              })}
            </div>
          )}
        </div>

        {selected ? (
          <FollowUpDetailPanel plan={selected} onApprove={() => onApprove(selected)} approvePending={approvePending} />
        ) : (
          <aside className="sdr-split__detail sdr-split__detail--empty hidden xl:flex">
            <div className="sdr-split__detail-placeholder">
              <Repeat className="h-8 w-8" aria-hidden />
              <p>Select a plan to review its touch timeline.</p>
            </div>
          </aside>
        )}
      </div>
    </section>
  )
}
