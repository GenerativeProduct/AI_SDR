import { Brain, RefreshCw, Search, Sparkles, Target } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { EnrichmentResult } from '../../api/types'
import { EmptyState, InlineBanner, ListLoading, WsSearchInput, WorkspaceSelect } from '../workspace'
import { EnrichmentDetailPanel } from './EnrichmentDetailPanel'
import { EnrichmentResultRow } from './EnrichmentResultRow'
import {
  averageConfidence,
  formatCount,
  highConfidenceCount,
  resultsWithSignals,
} from './enrichmentUtils'

type SelectOption = { value: string; label: string }

type EnrichmentResultsPanelProps = {
  results: EnrichmentResult[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  onRetry: () => void
  onRunResearch: () => void
  researchPending: boolean
}

export function EnrichmentResultsPanel({
  results,
  isLoading,
  isFetching,
  error,
  onRetry,
  onRunResearch,
  researchPending,
}: EnrichmentResultsPanelProps) {
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const statusOptions = useMemo<SelectOption[]>(() => {
    const statuses = [...new Set(results.map((result) => result.status).filter(Boolean))]
    return [{ value: '', label: 'All statuses' }, ...statuses.map((status) => ({ value: status, label: status }))]
  }, [results])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return results.filter((result) => {
      if (statusFilter && result.status !== statusFilter) return false
      if (!q) return true
      const haystack = [
        result.company_name,
        result.company_summary,
        result.recommended_next_action,
        ...(result.pain_point_hypotheses ?? []),
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [results, query, statusFilter])

  const selected =
    filtered.find((result) => (result.enrichment_id ?? result.account_id) === selectedId) ??
    filtered[0] ??
    null

  const selectedKey = selected ? (selected.enrichment_id ?? selected.account_id) : null

  const kpis = [
    {
      label: 'Enriched',
      value: formatCount(results.length),
      hint: 'Research results',
      icon: Brain,
    },
    {
      label: 'Avg confidence',
      value: `${averageConfidence(results)}%`,
      hint: 'Mean model confidence',
      icon: Target,
    },
    {
      label: 'High confidence',
      value: formatCount(highConfidenceCount(results)),
      hint: 'Scores at or above 70%',
      icon: Sparkles,
    },
    {
      label: 'With signals',
      value: formatCount(resultsWithSignals(results)),
      hint: 'Results containing live signals',
      icon: Search,
    },
  ]

  return (
    <section className="sdr-enrichment__results">
      <header className="sdr-enrichment__results-header">
        <div>
          <p className="ws-heading-section">Results</p>
          <h2 className="sdr-enrichment__pane-title">Enrichment library</h2>
          <p className="sdr-enrichment__pane-desc">
            Review research briefs, confidence scores, and downstream intelligence handoff.
          </p>
        </div>
        <button type="button" className="ws-btn ws-btn--secondary ws-btn--compact" disabled={isFetching} onClick={onRetry}>
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
          Refresh
        </button>
      </header>

      <div className="sdr-enrichment__kpi-row">
        {kpis.map((kpi) => (
          <article key={kpi.label} className="sdr-enrichment-kpi">
            <span className="sdr-enrichment-kpi__icon" aria-hidden>
              <kpi.icon className="h-4 w-4" />
            </span>
            <p className="ws-kpi-label">{kpi.label}</p>
            <p className="ws-kpi-value">{kpi.value}</p>
            <p className="ws-kpi-hint">{kpi.hint}</p>
          </article>
        ))}
      </div>

      <div className="sdr-enrichment__filters">
        <WsSearchInput value={query} onChange={setQuery} placeholder="Search enrichments…" aria-label="Search enrichment results" />
        <WorkspaceSelect
          id="enrichment-status-filter"
          label="Status"
          value={statusFilter}
          options={statusOptions}
          onChange={setStatusFilter}
        />
      </div>

      <div className="sdr-enrichment__results-split">
        <div className="sdr-enrichment__results-list-wrap">
          {error ? <InlineBanner message="Failed to load enrichments" onRetry={onRetry} /> : null}

          {isLoading ? (
            <ListLoading rows={5} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<Brain className="h-7 w-7" aria-hidden />}
              title={query || statusFilter ? 'No matching enrichments' : 'No enrichment results'}
              description={
                query || statusFilter
                  ? 'Try a different search term or clear filters.'
                  : 'Select a discovered account and run enrichment research.'
              }
              action={
                !query && !statusFilter ? (
                  <button type="button" className="ws-btn ws-btn--primary" disabled={researchPending} onClick={onRunResearch}>
                    Run research
                  </button>
                ) : null
              }
            />
          ) : (
            <div className="sdr-enrichment-result-list">
              {filtered.map((result) => {
                const key = result.enrichment_id ?? result.account_id
                return (
                  <EnrichmentResultRow
                    key={key}
                    result={result}
                    selected={selectedKey === key}
                    onSelect={() => setSelectedId(key)}
                  />
                )
              })}
            </div>
          )}
        </div>

        {selected ? (
          <EnrichmentDetailPanel result={selected} />
        ) : (
          <aside className="sdr-enrichment__detail sdr-enrichment__detail--empty hidden xl:flex">
            <div className="sdr-enrichment__detail-placeholder">
              <Brain className="h-8 w-8" aria-hidden />
              <p>Select an enrichment result to view the full research brief.</p>
            </div>
          </aside>
        )}
      </div>
    </section>
  )
}
