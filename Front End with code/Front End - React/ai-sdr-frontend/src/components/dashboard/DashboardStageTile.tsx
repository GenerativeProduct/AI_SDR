import type { LucideIcon } from 'lucide-react'

export type DashboardStageTileProps = {
  label: string
  icon: LucideIcon
  count: number
  max: number
  active?: boolean
}

function formatCount(value: number) {
  return value.toLocaleString()
}

export function DashboardStageTile({
  label,
  icon: Icon,
  count,
  max,
  active = false,
}: DashboardStageTileProps) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0
  const width = `${Math.max(pct, count > 0 ? 8 : 0)}%`

  return (
    <article
      className={`sdr-dash-stage-tile ${active ? 'sdr-dash-stage-tile--active' : ''}`}
      title={`${label}: ${formatCount(count)}`}
    >
      <div className="sdr-dash-stage-tile__head">
        <span className="sdr-dash-stage-tile__icon">
          <Icon className="h-4 w-4" aria-hidden />
        </span>
        <span className="sdr-dash-stage-tile__status">{active ? 'Active' : 'Idle'}</span>
      </div>
      <p className="sdr-dash-stage-tile__label">{label}</p>
      <p className="sdr-dash-stage-tile__value">{formatCount(count)}</p>
      <div className="ws-funnel-track sdr-dash-stage-tile__track" aria-hidden>
        <div className="ws-funnel-fill sdr-dash-stage-tile__fill" style={{ width }} />
      </div>
    </article>
  )
}
