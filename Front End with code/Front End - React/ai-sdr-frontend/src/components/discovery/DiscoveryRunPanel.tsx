import { CheckCircle2, CircleDashed, Loader2, Play, Zap } from 'lucide-react'
import { cn } from '../../lib/utils'
import { WorkspaceField, WorkspaceSelect } from '../workspace'

type SelectOption = { value: string; label: string }

type DiscoveryRunPanelProps = {
  icpOptions: SelectOption[]
  runIcpId: string
  runLimit: string
  onRunIcpChange: (value: string) => void
  onRunLimitChange: (value: string) => void
  onRun: () => void
  runPending: boolean
  onQuickRun: () => void
  quickRunPending: boolean
  jobId: string | null
  jobStatus?: string
  jobProgress?: number
  accountProviders?: boolean
  contactProvider?: string
}

export function DiscoveryRunPanel({
  icpOptions,
  runIcpId,
  runLimit,
  onRunIcpChange,
  onRunLimitChange,
  onRun,
  runPending,
  onQuickRun,
  quickRunPending,
  jobId,
  jobStatus,
  jobProgress = 0,
  accountProviders,
  contactProvider,
}: DiscoveryRunPanelProps) {
  const isRunning = Boolean(jobId && jobStatus && !['completed', 'failed'].includes(jobStatus))
  const providersReady = Boolean(accountProviders)

  return (
    <aside className="sdr-discovery__run">
      <header className="sdr-discovery__run-header">
        <div>
          <p className="ws-heading-section">Run</p>
          <h2 className="sdr-discovery__pane-title">Prospect discovery</h2>
          <p className="sdr-discovery__pane-desc">
            Match accounts and contacts against a saved ICP definition.
          </p>
        </div>
        <div className="sdr-discovery__status-strip" aria-live="polite">
          <span className={cn('sdr-discovery__status-chip', providersReady && 'sdr-discovery__status-chip--on')}>
            {providersReady ? <CheckCircle2 className="h-3.5 w-3.5" aria-hidden /> : <CircleDashed className="h-3.5 w-3.5" aria-hidden />}
            Providers
          </span>
          <span className={cn('sdr-discovery__status-chip', isRunning && 'sdr-discovery__status-chip--active')}>
            {isRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Play className="h-3.5 w-3.5" aria-hidden />}
            {isRunning ? 'Running' : 'Idle'}
          </span>
        </div>
      </header>

      <div className="sdr-discovery__run-body">
        <div className="sdr-discovery__provider-card">
          <p className="sdr-discovery__provider-card__label">Integration status</p>
          <dl className="sdr-discovery__provider-meta">
            <div>
              <dt>Account sources</dt>
              <dd>{providersReady ? 'Connected' : 'Waiting for provider'}</dd>
            </div>
            <div>
              <dt>Contact provider</dt>
              <dd>{contactProvider ?? 'Not configured'}</dd>
            </div>
          </dl>
        </div>

        <div className="sdr-discovery__form">
          <WorkspaceSelect
            id="discovery-run-icp"
            label="ICP definition"
            value={runIcpId}
            options={icpOptions}
            onChange={onRunIcpChange}
            placeholder="Select ICP…"
          />
          <WorkspaceField
            id="discovery-limit"
            label="Account limit"
            type="number"
            value={runLimit}
            onChange={onRunLimitChange}
            hint="Maximum accounts to discover per run"
          />
        </div>

        {jobId ? (
          <div className="sdr-discovery__progress-card">
            <div className="sdr-discovery__progress-head">
              <p className="sdr-discovery__progress-label">Active job</p>
              <p className="sdr-discovery__progress-value">{jobStatus ?? 'queued'} · {jobProgress}%</p>
            </div>
            <div className="sdr-discovery__progress-track" aria-hidden>
              <div className="sdr-discovery__progress-fill" style={{ width: `${Math.min(100, jobProgress)}%` }} />
            </div>
          </div>
        ) : null}

        <div className="sdr-discovery__run-toolbar">
          <button
            type="button"
            className="ws-btn ws-btn--primary w-full"
            disabled={!runIcpId || runPending || isRunning}
            onClick={onRun}
          >
            {runPending || isRunning ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Play className="h-4 w-4" aria-hidden />}
            Run discovery
          </button>
          <button
            type="button"
            className="ws-btn ws-btn--secondary w-full"
            disabled={quickRunPending || isRunning}
            onClick={onQuickRun}
          >
            <Zap className="h-4 w-4" aria-hidden />
            Quick sample run
          </button>
        </div>
      </div>
    </aside>
  )
}
