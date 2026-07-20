import { Brain, FlaskConical, RefreshCw, Sparkles, Target, TrendingUp } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { ProspectIntelligenceResult } from '../../api/types'
import { EmptyState, InlineBanner, ListLoading, WsSearchInput, WorkspaceSelect } from '../workspace'
import { IntelligenceDetailPanel } from './IntelligenceDetailPanel'
import { IntelligenceResultRow } from './IntelligenceResultRow'
import {
  averagePriorityScore,
  formatCount,
  highIntentCount,
  highPriorityCount,
} from './intelligenceUtils'

type SelectOption = { value: string; label: string }

type IntelligenceResultsPanelProps = {
  rows: ProspectIntelligenceResult[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  onRetry: () => void
  onAnalyze: () => void
  analyzePending: boolean
}

export function IntelligenceResultsPanel({
  rows,
  isLoading,
  isFetching,
  error,
  onRetry,
  onAnalyze,
  analyzePending,
}: IntelligenceResultsPanelProps) {
  const [query, setQuery] = useState('')
  const [bandFilter, setBandFilter] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const bandOptions = useMemo<SelectOption[]>(() => {
    const bands = [...new Set(rows.map((row) => row.ranking.priority_band).filter(Boolean))]
    return [{ value: '', label: 'All bands' }, ...bands.map((band) => ({ value: band, label: band }))]
  }, [rows])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return rows.filter((row) => {
      if (bandFilter && row.ranking.priority_band !== bandFilter) return false
      if (!q) return true
      const haystack = [row.contact_name, row.company_name, row.intent.level, row.ranking.priority_band]
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [rows, query, bandFilter])

  const selected =
    filtered.find((row) => (row.intelligence_id ?? `${row.account_id}-${row.contact_id}`) === selectedId) ??
    filtered[0] ??
    null

  const selectedKey = selected ? (selected.intelligence_id ?? `${selected.account_id}-${selected.contact_id}`) : null

  const kpis = [
    {
      label: 'Scored',
      value: formatCount(rows.length),
      hint: 'Intelligence records',
      icon: Brain,
    },
    {
      label: 'Avg priority',
      value: averagePriorityScore(rows).toFixed(1),
      hint: 'Mean ranking score',
      icon: Target,
    },
    {
      label: 'High priority',
      value: formatCount(highPriorityCount(rows)),
      hint: 'Top band prospects',
      icon: Sparkles,
    },
    {
      label: 'High intent',
      value: formatCount(highIntentCount(rows)),
      hint: 'Strong buying signals',
      icon: TrendingUp,
    },
  ]

  return (
    <section className="sdr-intelligence__results">
      <header className="sdr-intelligence__results-header">
        <div>
          <p className="ws-heading-section">Results</p>
          <h2 className="sdr-intelligence__pane-title">Intelligence library</h2>
          <p className="sdr-intelligence__pane-desc">
            Compare intent, propensity, and priority scores before qualification and outreach.
          </p>
        </div>
        <button type="button" className="ws-btn ws-btn--secondary ws-btn--compact" disabled={isFetching} onClick={onRetry}>
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
          Refresh
        </button>
      </header>

      <div className="sdr-intelligence__kpi-row">
        {kpis.map((kpi) => (
          <article key={kpi.label} className="sdr-intelligence-kpi">
            <span className="sdr-intelligence-kpi__icon" aria-hidden>
              <kpi.icon className="h-4 w-4" />
            </span>
            <p className="ws-kpi-label">{kpi.label}</p>
            <p className="ws-kpi-value">{kpi.value}</p>
            <p className="ws-kpi-hint">{kpi.hint}</p>
          </article>
        ))}
      </div>

      <div className="sdr-intelligence__filters">
        <WsSearchInput value={query} onChange={setQuery} placeholder="Search prospects…" aria-label="Search intelligence results" />
        <WorkspaceSelect
          id="intel-band-filter"
          label="Priority band"
          value={bandFilter}
          options={bandOptions}
          onChange={setBandFilter}
        />
      </div>

      <div className="sdr-intelligence__results-split">
        <div className="sdr-intelligence__results-list-wrap">
          {error ? <InlineBanner message="Failed to load intelligence" onRetry={onRetry} /> : null}

          {isLoading ? (
            <ListLoading rows={5} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<Brain className="h-7 w-7" aria-hidden />}
              title={query || bandFilter ? 'No matching records' : 'No intelligence records'}
              description={
                query || bandFilter
                  ? 'Try a different search term or clear filters.'
                  : 'Select a contact and run prospect analysis.'
              }
              action={
                !query && !bandFilter ? (
                  <button type="button" className="ws-btn ws-btn--primary" disabled={analyzePending} onClick={onAnalyze}>
                    Analyze prospect
                  </button>
                ) : null
              }
            />
          ) : (
            <div className="sdr-intelligence-result-list">
              {filtered.map((row) => {
                const key = row.intelligence_id ?? `${row.account_id}-${row.contact_id}`
                return (
                  <IntelligenceResultRow
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
          <IntelligenceDetailPanel row={selected} />
        ) : (
          <aside className="sdr-intelligence__detail sdr-intelligence__detail--empty hidden xl:flex">
            <div className="sdr-intelligence__detail-placeholder">
              <FlaskConical className="h-8 w-8" aria-hidden />
              <p>Select a scored prospect to view intent, propensity, and ranking detail.</p>
            </div>
          </aside>
        )}
      </div>
    </section>
  )
}
