import { Brain, CheckCircle2, CircleDashed, Loader2, Sparkles, UserRound } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { DiscoveredContact } from '../../api/types'
import { WorkspaceSelect } from '../workspace'

type SelectOption = { value: string; label: string }

type IntelligenceAnalyzePanelProps = {
  contactId: string
  contactOptions: SelectOption[]
  selectedContact?: DiscoveredContact
  companyName?: string
  onContactChange: (value: string) => void
  onAnalyze: () => void
  analyzePending: boolean
  rankingReady?: boolean
  rankingDetail?: string
  enrichmentAvailable?: boolean
}

export function IntelligenceAnalyzePanel({
  contactId,
  contactOptions,
  selectedContact,
  companyName,
  onContactChange,
  onAnalyze,
  analyzePending,
  rankingReady,
  rankingDetail,
  enrichmentAvailable,
}: IntelligenceAnalyzePanelProps) {
  return (
    <aside className="sdr-intelligence__analyze">
      <header className="sdr-intelligence__analyze-header">
        <div>
          <p className="ws-heading-section">Analyze</p>
          <h2 className="sdr-intelligence__pane-title">Prospect intelligence</h2>
          <p className="sdr-intelligence__pane-desc">
            Score intent, reply propensity, and priority ranking for outbound targeting.
          </p>
        </div>
        <div className="sdr-intelligence__status-strip" aria-live="polite">
          <span className={cn('sdr-intelligence__status-chip', rankingReady && 'sdr-intelligence__status-chip--on')}>
            {rankingReady ? <CheckCircle2 className="h-3.5 w-3.5" aria-hidden /> : <CircleDashed className="h-3.5 w-3.5" aria-hidden />}
            Ranking
          </span>
          <span className={cn('sdr-intelligence__status-chip', analyzePending && 'sdr-intelligence__status-chip--active')}>
            {analyzePending ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Brain className="h-3.5 w-3.5" aria-hidden />}
            {analyzePending ? 'Running' : 'Idle'}
          </span>
        </div>
      </header>

      <div className="sdr-intelligence__analyze-body">
        <div className="sdr-intelligence__provider-card">
          <p className="sdr-intelligence__provider-card__label">Model status</p>
          <dl className="sdr-intelligence__provider-meta">
            <div>
              <dt>Ranking engine</dt>
              <dd>{rankingReady ? 'Ready' : 'Waiting for models'}</dd>
            </div>
            <div>
              <dt>Detail</dt>
              <dd>{rankingDetail ?? 'Not configured'}</dd>
            </div>
            <div>
              <dt>Enrichment context</dt>
              <dd>{enrichmentAvailable ? 'Available' : 'Run enrichment first'}</dd>
            </div>
          </dl>
        </div>

        <div className="sdr-intelligence__form">
          <WorkspaceSelect
            id="intel-contact"
            label="Contact"
            value={contactId}
            options={contactOptions}
            onChange={onContactChange}
            placeholder="Select contact…"
          />

          {selectedContact ? (
            <div className="sdr-intelligence__contact-preview">
              <span className="sdr-intelligence__contact-preview__icon" aria-hidden>
                <UserRound className="h-4 w-4" />
              </span>
              <div className="min-w-0">
                <p className="sdr-intelligence__contact-preview__name">{selectedContact.full_name}</p>
                <p className="sdr-intelligence__contact-preview__meta">
                  {selectedContact.title} · {companyName ?? 'Unknown company'}
                </p>
              </div>
              <span className="sdr-intelligence__match-pill">{selectedContact.persona_match_score}% match</span>
            </div>
          ) : null}
        </div>

        <button
          type="button"
          className="ws-btn ws-btn--primary w-full"
          disabled={!contactId || analyzePending}
          onClick={onAnalyze}
        >
          {analyzePending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Sparkles className="h-4 w-4" aria-hidden />}
          Analyze prospect
        </button>
      </div>
    </aside>
  )
}
