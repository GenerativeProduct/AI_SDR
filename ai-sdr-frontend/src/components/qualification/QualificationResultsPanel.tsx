import { FlaskConical, RefreshCw, Target, TrendingUp, UserCheck } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { QualificationResult } from '../../api/types'
import {
  EmptyState,
  FilterBar,
  InlineBanner,
  ListLoading,
  WsSearchInput,
} from '../workspace'
import { QualificationDetailPanel } from './QualificationDetailPanel'
import { QualificationResultRow, qualificationKey } from './QualificationResultRow'
import {
  QUALIFICATION_FILTERS,
  averageQualificationScore,
  countByStatus,
  formatCount,
  salesReadyCount,
} from './qualificationUtils'

type QualificationResultsPanelProps = {
  results: QualificationResult[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  statusFilter: string
  onStatusFilterChange: (value: string) => void
  onRetry: () => void
  onEvaluate: () => void
  evaluatePending: boolean
}

export function QualificationResultsPanel({
  results,
  isLoading,
  isFetching,
  error,
  statusFilter,
  onStatusFilterChange,
  onRetry,
  onEvaluate,
  evaluatePending,
}: QualificationResultsPanelProps) {
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const filterOptions = QUALIFICATION_FILTERS.map((option) => ({
    ...option,
    count: option.id === 'all' ? results.length : countByStatus(results, option.id as QualificationResult['qualification_status']),
  }))

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return results.filter((row) => {
      if (statusFilter !== 'all' && row.qualification_status !== statusFilter) return false
      if (!q) return true
      return [row.contact_name, row.company_name, row.next_action, row.qualification_status]
        .join(' ')
        .toLowerCase()
        .includes(q)
    })
  }, [results, query, statusFilter])

  const selected =
    filtered.find((row) => qualificationKey(row) === selectedId) ?? filtered[0] ?? null

  const selectedKey = selected ? qualificationKey(selected) : null

  const kpis = [
    { label: 'Qualified', value: formatCount(results.length), hint: 'Total evaluations', icon: FlaskConical },
    { label: 'SQL', value: formatCount(countByStatus(results, 'SQL')), hint: 'Sales qualified leads', icon: Target },
    { label: 'Sales ready', value: formatCount(salesReadyCount(results)), hint: 'Ready for outreach', icon: UserCheck },
    { label: 'Avg score', value: String(averageQualificationScore(results)), hint: 'Mean qualification score', icon: TrendingUp },
  ]

  return (
    <section className="sdr-qualification__results">
      <header className="sdr-qualification__results-header">
        <div>
          <p className="ws-heading-section">Results</p>
          <h2 className="sdr-qualification__pane-title">Qualification queue</h2>
          <p className="sdr-qualification__pane-desc">Filter by tier, inspect BANT/MEDDIC breakdowns, and route SQLs to outreach.</p>
        </div>
        <button type="button" className="ws-btn ws-btn--secondary ws-btn--compact" disabled={isFetching} onClick={onRetry}>
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
          Refresh
        </button>
      </header>

      <div className="sdr-qualification__kpi-row">
        {kpis.map((kpi) => (
          <article key={kpi.label} className="sdr-qualification-kpi">
            <span className="sdr-qualification-kpi__icon" aria-hidden>
              <kpi.icon className="h-4 w-4" />
            </span>
            <p className="ws-kpi-label">{kpi.label}</p>
            <p className="ws-kpi-value">{kpi.value}</p>
            <p className="ws-kpi-hint">{kpi.hint}</p>
          </article>
        ))}
      </div>

      <div className="sdr-qualification__filters">
        <WsSearchInput value={query} onChange={setQuery} placeholder="Search qualifications…" aria-label="Search qualifications" />
        <FilterBar options={filterOptions} activeId={statusFilter} onChange={onStatusFilterChange} aria-label="Qualification status" />
      </div>

      <div className="sdr-qualification__results-split">
        <div className="sdr-qualification__results-list-wrap">
          {error ? <InlineBanner message="Failed to load qualifications" onRetry={onRetry} /> : null}

          {isLoading ? (
            <ListLoading rows={5} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<FlaskConical className="h-7 w-7" aria-hidden />}
              title={query || statusFilter !== 'all' ? 'No matching qualifications' : 'No qualifications yet'}
              description={
                query || statusFilter !== 'all'
                  ? 'Try a different search term or filter.'
                  : 'Select a contact and run BANT / MEDDIC evaluation.'
              }
              action={
                !query && statusFilter === 'all' ? (
                  <button type="button" className="ws-btn ws-btn--primary" disabled={evaluatePending} onClick={onEvaluate}>
                    Evaluate contact
                  </button>
                ) : null
              }
            />
          ) : (
            <div className="sdr-qualification-result-list">
              {filtered.map((row) => {
                const key = qualificationKey(row)
                return (
                  <QualificationResultRow
                    key={key}
                    row={row}
                    selected={selectedKey === key}
                    onSelect={() => setSelectedId(key)}
                  />
                )
              })}
            </div>
          )}
        </div>

        {selected ? (
          <QualificationDetailPanel row={selected} />
        ) : (
          <aside className="sdr-qualification__detail sdr-qualification__detail--empty hidden xl:flex">
            <div className="sdr-qualification__detail-placeholder">
              <FlaskConical className="h-8 w-8" aria-hidden />
              <p>Select a qualification to inspect framework scores and reasoning.</p>
            </div>
          </aside>
        )}
      </div>
    </section>
  )
}
