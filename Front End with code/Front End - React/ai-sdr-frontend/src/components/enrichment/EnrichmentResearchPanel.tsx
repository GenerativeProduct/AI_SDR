import { Brain, CheckCircle2, CircleDashed, Loader2, Search, Users } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { DiscoveredAccount } from '../../api/types'
import { WorkspaceSelect, WsSwitch } from '../workspace'

type SelectOption = { value: string; label: string }

type EnrichmentResearchPanelProps = {
  accountId: string
  accountOptions: SelectOption[]
  selectedAccount?: DiscoveredAccount
  contactCount: number
  useLlm: boolean
  onAccountChange: (value: string) => void
  onUseLlmChange: (value: boolean) => void
  onResearch: () => void
  researchPending: boolean
  liveSearchConfigured?: boolean
  statusDetail?: string
}

export function EnrichmentResearchPanel({
  accountId,
  accountOptions,
  selectedAccount,
  contactCount,
  useLlm,
  onAccountChange,
  onUseLlmChange,
  onResearch,
  researchPending,
  liveSearchConfigured,
  statusDetail,
}: EnrichmentResearchPanelProps) {
  const providersReady = Boolean(liveSearchConfigured)

  return (
    <aside className="sdr-enrichment__research">
      <header className="sdr-enrichment__research-header">
        <div>
          <p className="ws-heading-section">Research</p>
          <h2 className="sdr-enrichment__pane-title">Account enrichment</h2>
          <p className="sdr-enrichment__pane-desc">
            Deep research on discovered accounts — summaries, signals, and personalization angles.
          </p>
        </div>
        <div className="sdr-enrichment__status-strip" aria-live="polite">
          <span className={cn('sdr-enrichment__status-chip', providersReady && 'sdr-enrichment__status-chip--on')}>
            {providersReady ? <CheckCircle2 className="h-3.5 w-3.5" aria-hidden /> : <CircleDashed className="h-3.5 w-3.5" aria-hidden />}
            Search
          </span>
          <span className={cn('sdr-enrichment__status-chip', researchPending && 'sdr-enrichment__status-chip--active')}>
            {researchPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Brain className="h-3.5 w-3.5" aria-hidden />}
            {researchPending ? 'Running' : 'Idle'}
          </span>
        </div>
      </header>

      <div className="sdr-enrichment__research-body">
        <div className="sdr-enrichment__provider-card">
          <p className="sdr-enrichment__provider-card__label">Integration status</p>
          <dl className="sdr-enrichment__provider-meta">
            <div>
              <dt>Live search</dt>
              <dd>{providersReady ? 'Configured' : 'Not configured'}</dd>
            </div>
            <div>
              <dt>Detail</dt>
              <dd>{statusDetail ?? 'Waiting for provider'}</dd>
            </div>
          </dl>
        </div>

        <div className="sdr-enrichment__form">
          <WorkspaceSelect
            id="enrichment-account"
            label="Discovered account"
            value={accountId}
            options={accountOptions}
            onChange={onAccountChange}
            placeholder="Select account…"
          />

          {selectedAccount ? (
            <div className="sdr-enrichment__account-preview">
              <span className="sdr-enrichment__account-preview__icon" aria-hidden>
                <Search className="h-4 w-4" />
              </span>
              <div className="min-w-0">
                <p className="sdr-enrichment__account-preview__name">{selectedAccount.company_name}</p>
                <p className="sdr-enrichment__account-preview__meta">
                  {selectedAccount.industry} · Fit {selectedAccount.fit_score}/100
                </p>
              </div>
              <span className="sdr-enrichment__contacts-pill">
                <Users className="h-3.5 w-3.5" aria-hidden />
                {contactCount}
              </span>
            </div>
          ) : null}

          <WsSwitch
            id="enrichment-use-llm"
            checked={useLlm}
            onChange={onUseLlmChange}
            disabled={researchPending}
            label="Use Ollama for research"
            description="Run local LLM synthesis for company summaries and pain-point hypotheses."
          />
        </div>

        <button
          type="button"
          className="ws-btn ws-btn--primary w-full"
          disabled={!accountId || researchPending}
          onClick={onResearch}
        >
          {researchPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Brain className="h-4 w-4" aria-hidden />}
          Run enrichment research
        </button>
      </div>
    </aside>
  )
}
