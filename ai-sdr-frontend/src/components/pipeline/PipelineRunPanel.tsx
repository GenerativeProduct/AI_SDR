import { Sparkles } from 'lucide-react'
import type { JobStatusResponse, SDRPipelineResponse } from '../../api/types'
import { EmptyState, InlineBanner } from '../workspace'
import { PipelineResults } from './PipelineResults'
import { PipelineStageRail } from './PipelineStageRail'

type PipelineRunPanelProps = {
  jobId: string | null
  job?: JobStatusResponse
  result?: SDRPipelineResponse
  hasPrompt: boolean
}

export function PipelineRunPanel({ jobId, job, result, hasPrompt }: PipelineRunPanelProps) {
  const isRunning = Boolean(jobId && job && job.status !== 'completed' && job.status !== 'failed')
  const progress = job?.progress ?? (result ? 100 : 0)
  const failed = job?.status === 'failed'

  return (
    <section className="sdr-pipeline__run" aria-live="polite">
      <header className="sdr-pipeline__run-header">
        <div>
          <p className="ws-heading-section">Run output</p>
          <h2 className="sdr-pipeline__pane-title">
            {result ? 'Pipeline results' : isRunning ? 'Agents running' : 'Ready to execute'}
          </h2>
          <p className="sdr-pipeline__pane-desc">
            {result
              ? 'Review stage outputs, approve outreach, and jump into ops modules.'
              : isRunning
                ? 'Seven agent stages execute sequentially from ICP through follow-up.'
                : 'Compose an ICP on the left, then run the full SDR agent chain.'}
          </p>
        </div>
        {isRunning || result ? (
          <div className="sdr-pipeline__run-meta">
            <span className="sdr-pipeline__run-meta__label">Progress</span>
            <span className="sdr-pipeline__run-meta__value">{Math.round(progress)}%</span>
          </div>
        ) : null}
      </header>

      {isRunning ? (
        <div className="sdr-pipeline__progress-card">
          <div className="sdr-pipeline__progress-track" aria-hidden>
            <span className="sdr-pipeline__progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <p className="sdr-pipeline__progress-status">
            {job?.status ?? 'queued'} · stage {Math.min(7, Math.floor((progress / 100) * 7) + 1)} of 7
          </p>
          <PipelineStageRail progress={progress} />
        </div>
      ) : null}

      {failed ? (
        <InlineBanner variant="error" message={job?.error ?? 'The pipeline job failed. Adjust your ICP and try again.'} />
      ) : null}

      <div className="sdr-pipeline__run-body">
        {result ? (
          <PipelineResults result={result} embedded />
        ) : !isRunning && !failed ? (
          <div className="sdr-pipeline__idle">
            <EmptyState
              icon={<Sparkles className="h-7 w-7" aria-hidden />}
              title={hasPrompt ? 'ICP drafted — run the pipeline' : 'Start with a target market prompt'}
              description={
                hasPrompt
                  ? 'Validate your ICP or run the pipeline to discover accounts, enrich prospects, and draft outreach.'
                  : 'Describe who you sell to in plain language. The agent chain handles discovery through follow-up.'
              }
            />
            <div className="sdr-pipeline__idle-rail">
              <p className="sdr-pipeline__idle-rail__label">Agent stages</p>
              <PipelineStageRail progress={0} variant="compact" />
            </div>
          </div>
        ) : null}
      </div>
    </section>
  )
}
