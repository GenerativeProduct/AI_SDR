import { cn } from '../../lib/utils'
import { PIPELINE_STAGES, stageIndexFromProgress } from './pipelineStages'

type PipelineStageRailProps = {
  progress?: number
  variant?: 'compact' | 'detailed'
  className?: string
}

export function PipelineStageRail({
  progress = 0,
  variant = 'detailed',
  className,
}: PipelineStageRailProps) {
  const activeIndex = stageIndexFromProgress(progress)
  const isRunning = progress > 0 && progress < 100
  const isComplete = progress >= 100

  return (
    <ol className={cn('sdr-pipeline-rail', variant === 'compact' && 'sdr-pipeline-rail--compact', className)} aria-label="Pipeline stages">
      {PIPELINE_STAGES.map((stage, index) => {
        const Icon = stage.icon
        const complete = isComplete || index < activeIndex
        const active = isRunning && index === activeIndex

        return (
          <li
            key={stage.id}
            className={cn(
              'sdr-pipeline-rail__step',
              complete && 'sdr-pipeline-rail__step--complete',
              active && 'sdr-pipeline-rail__step--active',
            )}
          >
            <span className="sdr-pipeline-rail__node" aria-hidden>
              <Icon className="h-3.5 w-3.5" />
            </span>
            <div className="sdr-pipeline-rail__copy min-w-0">
              <p className="sdr-pipeline-rail__label">{variant === 'compact' ? stage.shortLabel : stage.label}</p>
              {variant === 'detailed' ? (
                <p className="sdr-pipeline-rail__detail">
                  {complete ? 'Complete' : active ? 'Running…' : 'Waiting'}
                </p>
              ) : null}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
