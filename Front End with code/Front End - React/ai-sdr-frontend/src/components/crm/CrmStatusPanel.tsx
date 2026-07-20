import { Plug, RefreshCw } from 'lucide-react'

type CrmStatusPanelProps = {
  status?: Record<string, unknown>
  isLoading: boolean
  onRetry: () => void
}

export function CrmStatusPanel({ status, isLoading, onRetry }: CrmStatusPanelProps) {
  const connected = Boolean(status && Object.keys(status).length > 0)

  return (
    <aside className="sdr-split__left">
      <header className="sdr-split__left-header">
        <div>
          <p className="ws-heading-section">Provider</p>
          <h2 className="sdr-split__pane-title">CRM status</h2>
          <p className="sdr-split__pane-desc">Integration health and provider configuration.</p>
        </div>
        <span className={`sdr-split__status-chip ${connected ? 'sdr-split__status-chip--on' : ''}`}>
          <Plug className="h-3 w-3" aria-hidden />
          {connected ? 'Connected' : 'Unknown'}
        </span>
      </header>

      <div className="sdr-split__left-body">
        <div className="sdr-split__meta-card">
          <p className="sdr-split__meta-card__label">Provider snapshot</p>
          <pre className="mt-2 max-h-80 overflow-auto text-xs leading-relaxed text-[var(--ws-text-muted)]">
            {JSON.stringify(status ?? { loading: isLoading }, null, 2)}
          </pre>
        </div>

        <button type="button" className="ws-btn ws-btn--secondary w-full" onClick={onRetry}>
          <RefreshCw className="h-4 w-4" aria-hidden />
          Refresh status
        </button>
      </div>
    </aside>
  )
}
