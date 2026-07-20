import { cn } from '../../lib/utils'

const PIPELINE_STEPS = [
  'ICP',
  'Discovery',
  'Enrichment',
  'Intelligence',
  'Qualification',
  'Outreach',
  'Follow-Up',
] as const

export function PipelineStepper({ progress }: { progress: number }) {
  const activeIndex = Math.min(
    PIPELINE_STEPS.length - 1,
    Math.floor((progress / 100) * PIPELINE_STEPS.length),
  )

  return (
    <ol className="mt-4 flex flex-wrap gap-2" aria-label="Pipeline progress">
      {PIPELINE_STEPS.map((step, index) => (
        <li
          key={step}
          className={cn(
            'rounded-full px-3 py-1 text-xs font-medium',
            index < activeIndex && 'bg-success-muted text-success-foreground',
            index === activeIndex && 'bg-accent-muted text-accent',
            index > activeIndex && 'bg-overlay text-text-subtle',
          )}
        >
          {step}
        </li>
      ))}
    </ol>
  )
}

export function ProviderChip({
  label,
  ok,
  detail,
}: {
  label: string
  ok: boolean
  detail?: string
}) {
  return (
    <div
      className={cn(
        'rounded-lg border px-3 py-2 text-sm',
        ok
          ? 'border-success/20 bg-success-muted text-success-foreground'
          : 'border-warning/20 bg-warning-muted text-warning-foreground',
      )}
      title={detail}
    >
      <span className="font-medium">{label}</span>
      <span className="ml-2 text-2xs opacity-80">{ok ? 'Ready' : 'Not configured'}</span>
    </div>
  )
}
