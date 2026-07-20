import { CheckCircle2, Loader2, Sparkles, Wand2 } from 'lucide-react'
import type { ICPSuggestionResponse, ICPValidationResult } from '../../api/types'
import { cn } from '../../lib/utils'
import { WsControlField, WsSwitch, WsTextarea } from '../workspace'
import { PIPELINE_EXAMPLE_PROMPTS } from './pipelineStages'

type PipelineComposerPanelProps = {
  prompt: string
  onPromptChange: (value: string) => void
  syncMode: boolean
  onSyncModeChange: (value: boolean) => void
  suggestion: ICPSuggestionResponse | null
  validation: ICPValidationResult | null
  onSuggest: () => void
  onValidate: () => void
  onRun: () => void
  suggestPending: boolean
  validatePending: boolean
  runPending: boolean
  isRunning: boolean
}

export function PipelineComposerPanel({
  prompt,
  onPromptChange,
  syncMode,
  onSyncModeChange,
  suggestion,
  validation,
  onSuggest,
  onValidate,
  onRun,
  suggestPending,
  validatePending,
  runPending,
  isRunning,
}: PipelineComposerPanelProps) {
  const canRun = Boolean(prompt.trim())
  const busy = suggestPending || validatePending || runPending || isRunning

  return (
    <aside className="sdr-pipeline__composer">
      <header className="sdr-pipeline__composer-header">
        <div>
          <p className="ws-heading-section">Composer</p>
          <h2 className="sdr-pipeline__pane-title">Describe your ICP</h2>
          <p className="sdr-pipeline__pane-desc">
            Natural language in — validated ICP and full agent pipeline out.
          </p>
        </div>
        <div className="sdr-pipeline__status-strip" aria-live="polite">
          <span className={cn('sdr-pipeline__status-chip', suggestion && 'sdr-pipeline__status-chip--on')}>
            <Sparkles className="h-3.5 w-3.5" aria-hidden />
            Suggested
          </span>
          <span className={cn('sdr-pipeline__status-chip', validation && 'sdr-pipeline__status-chip--on')}>
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
            Validated
          </span>
          <span className={cn('sdr-pipeline__status-chip', isRunning && 'sdr-pipeline__status-chip--active')}>
            {isRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Wand2 className="h-3.5 w-3.5" aria-hidden />}
            Running
          </span>
        </div>
      </header>

      <div className="sdr-pipeline__composer-body">
        <div className="sdr-pipeline__prompt-shell">
          <WsControlField
            id="pipeline-prompt"
            label="Target market prompt"
            hint="Describe your ideal customer in natural language."
          >
            <WsTextarea
              id="pipeline-prompt"
              value={prompt}
              onChange={(e) => onPromptChange(e.target.value)}
              rows={6}
              resize="vertical"
              disabled={busy}
              placeholder="e.g. Mid-market SaaS companies in the US with RevOps leaders struggling with pipeline visibility"
            />
          </WsControlField>
          <div className="sdr-pipeline__examples">
            <p className="sdr-pipeline__examples-label">Try an example</p>
            <div className="sdr-pipeline__example-list">
              {PIPELINE_EXAMPLE_PROMPTS.map((example) => (
                <button
                  key={example}
                  type="button"
                  className="sdr-pipeline__example-chip ws-focus-ring"
                  onClick={() => onPromptChange(example)}
                  disabled={busy}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="sdr-pipeline__toolbar">
          <div className="sdr-pipeline__toolbar-actions">
            <button type="button" className="ws-btn ws-btn--secondary" onClick={onSuggest} disabled={!canRun || busy}>
              {suggestPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Sparkles className="h-4 w-4" aria-hidden />}
              Suggest ICP
            </button>
            <button type="button" className="ws-btn ws-btn--secondary" onClick={onValidate} disabled={!canRun || busy}>
              {validatePending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : null}
              Validate
            </button>
            <button type="button" className="ws-btn ws-btn--primary" onClick={onRun} disabled={!canRun || busy}>
              {runPending || isRunning ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Wand2 className="h-4 w-4" aria-hidden />}
              Run pipeline
            </button>
          </div>
          <WsSwitch
            id="pipeline-sync-mode"
            checked={syncMode}
            onChange={onSyncModeChange}
            disabled={busy}
            label="Sync mode (dev)"
            description="Run the pipeline synchronously for local debugging."
          />
        </div>

        {suggestion ? (
          <article className="sdr-pipeline__insight-card">
            <header className="sdr-pipeline__insight-card__header">
              <p className="ws-heading-section">LLM reasoning</p>
              <span className="sdr-pipeline__insight-badge">{suggestion.source}</span>
            </header>
            <p className="sdr-pipeline__insight-card__body">{suggestion.reasoning}</p>
            <dl className="sdr-pipeline__insight-meta">
              <div>
                <dt>Personas</dt>
                <dd>{suggestion.personas.join(', ') || '—'}</dd>
              </div>
              <div>
                <dt>Pain points</dt>
                <dd>{suggestion.pain_points.join(', ') || '—'}</dd>
              </div>
            </dl>
          </article>
        ) : null}

        {validation ? (
          <article className="sdr-pipeline__insight-card sdr-pipeline__insight-card--validation">
            <header className="sdr-pipeline__insight-card__header">
              <p className="ws-heading-section">Validation</p>
              <span
                className={cn(
                  'sdr-pipeline__validation-pill',
                  validation.status === 'ok' && 'sdr-pipeline__validation-pill--ok',
                )}
              >
                {validation.status}
              </span>
            </header>
            {validation.warnings?.length ? (
              <ul className="sdr-pipeline__warning-list">
                {validation.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : (
              <p className="sdr-pipeline__insight-card__body">ICP payload is ready to run.</p>
            )}
          </article>
        ) : null}
      </div>
    </aside>
  )
}
