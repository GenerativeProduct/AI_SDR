import { FlaskConical, Loader2, Target, UserRound } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { DiscoveredContact } from '../../api/types'
import { WorkspaceSelect } from '../workspace'

type SelectOption = { value: string; label: string }

type QualificationEvaluatePanelProps = {
  contactId: string
  contactOptions: SelectOption[]
  selectedContact?: DiscoveredContact
  hasIntelligence: boolean
  hasEnrichment: boolean
  onContactChange: (value: string) => void
  onEvaluate: () => void
  evaluatePending: boolean
}

export function QualificationEvaluatePanel({
  contactId,
  contactOptions,
  selectedContact,
  hasIntelligence,
  hasEnrichment,
  onContactChange,
  onEvaluate,
  evaluatePending,
}: QualificationEvaluatePanelProps) {
  const contextReady = hasIntelligence || hasEnrichment

  return (
    <aside className="sdr-qualification__evaluate">
      <header className="sdr-qualification__evaluate-header">
        <div>
          <p className="ws-heading-section">Evaluate</p>
          <h2 className="sdr-qualification__pane-title">Contact qualification</h2>
          <p className="sdr-qualification__pane-desc">
            Score prospects with BANT and MEDDIC using enrichment and intelligence context.
          </p>
        </div>
        <div className="sdr-qualification__status-strip" aria-live="polite">
          <span className={cn('sdr-qualification__status-chip', hasEnrichment && 'sdr-qualification__status-chip--on')}>
            Enrichment
          </span>
          <span className={cn('sdr-qualification__status-chip', hasIntelligence && 'sdr-qualification__status-chip--on')}>
            Intelligence
          </span>
        </div>
      </header>

      <div className="sdr-qualification__evaluate-body">
        <div className="sdr-qualification__context-card">
          <p className="sdr-qualification__context-card__label">Context readiness</p>
          <dl className="sdr-qualification__context-meta">
            <div>
              <dt>Enrichment brief</dt>
              <dd>{hasEnrichment ? 'Available' : 'Missing'}</dd>
            </div>
            <div>
              <dt>Intelligence score</dt>
              <dd>{hasIntelligence ? 'Available' : 'Missing'}</dd>
            </div>
          </dl>
        </div>

        <div className="sdr-qualification__form">
          <WorkspaceSelect
            id="qual-contact"
            label="Contact"
            value={contactId}
            options={contactOptions}
            onChange={onContactChange}
            placeholder="Select contact…"
          />

          {selectedContact ? (
            <div className="sdr-qualification__contact-preview">
              <span className="sdr-qualification__contact-preview__icon" aria-hidden>
                <UserRound className="h-4 w-4" />
              </span>
              <div className="min-w-0">
                <p className="sdr-qualification__contact-preview__name">{selectedContact.full_name}</p>
                <p className="sdr-qualification__contact-preview__meta">{selectedContact.title}</p>
              </div>
              <span className="sdr-qualification__fit-pill">
                <Target className="h-3.5 w-3.5" aria-hidden />
                {selectedContact.persona_match_score}%
              </span>
            </div>
          ) : null}
        </div>

        <button
          type="button"
          className="ws-btn ws-btn--primary w-full"
          disabled={!contactId || evaluatePending}
          onClick={onEvaluate}
        >
          {evaluatePending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <FlaskConical className="h-4 w-4" aria-hidden />}
          Run BANT / MEDDIC
        </button>

        {!contextReady && contactId ? (
          <p className="sdr-qualification__hint">
            Limited context — run enrichment and intelligence first for stronger scoring.
          </p>
        ) : null}
      </div>
    </aside>
  )
}
