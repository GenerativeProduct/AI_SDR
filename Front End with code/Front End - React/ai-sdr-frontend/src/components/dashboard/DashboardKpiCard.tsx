import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'

export type DashboardKpiCardProps = {
  label: string
  value: number
  hint: string
  icon: LucideIcon
  tone?: 'default' | 'risk' | 'success'
  badge?: string
  to?: string
}

function formatCount(value: number) {
  return value.toLocaleString()
}

export function DashboardKpiCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = 'default',
  badge,
  to,
}: DashboardKpiCardProps) {
  const body = (
    <>
      <div className="sdr-kpi-card__accent" aria-hidden />
      <div className="sdr-kpi-card__head">
        <span className="sdr-kpi-card__icon">
          <Icon className="h-5 w-5" aria-hidden />
        </span>
        {badge ? <span className={`sdr-kpi-card__badge sdr-kpi-card__badge--${tone}`}>{badge}</span> : null}
      </div>
      <p className="ws-kpi-label">{label}</p>
      <p className="ws-kpi-value">{formatCount(value)}</p>
      <p className="ws-kpi-hint">{hint}</p>
      {to ? (
        <span className="sdr-kpi-card__link-hint">View module</span>
      ) : null}
    </>
  )

  if (to) {
    return (
      <Link to={to} className={`sdr-kpi-card sdr-kpi-card--${tone} group`}>
        {body}
      </Link>
    )
  }

  return <article className={`sdr-kpi-card sdr-kpi-card--${tone}`}>{body}</article>
}
