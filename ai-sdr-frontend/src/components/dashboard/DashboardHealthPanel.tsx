import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  CircleDashed,
  Mail,
  Megaphone,
  RefreshCw,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

type ReadinessItem = {
  label: string
  ok: boolean
  detail: string
}

type RevenueMetric = {
  label: string
  value: number
  icon: LucideIcon
}

function formatCount(value: number) {
  return value.toLocaleString()
}

function truncate(text: string, max = 40) {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

const quickActions = [
  { label: 'Discovery flow', to: '/discovery' },
  { label: 'Outreach queue', to: '/outreach' },
  { label: 'Meetings + CRM', to: '/meetings' },
] as const

export function DashboardHealthPanel({
  readiness,
  revenue,
}: {
  readiness: ReadinessItem[]
  revenue: RevenueMetric[]
}) {
  const readyCount = readiness.filter((item) => item.ok).length
  const total = Math.max(readiness.length, 1)
  const pct = Math.round((readyCount / total) * 100)
  const revenueMax = Math.max(1, ...revenue.map((item) => item.value))

  return (
    <div className="sdr-health-body">
      <section className="sdr-health-section sdr-health-section--readiness">
        <div className="sdr-health-score" aria-label={`${readyCount} of ${total} systems ready`}>
          <div
            className="sdr-health-score__ring"
            style={{ '--sdr-health-pct': `${pct}%` } as CSSProperties}
          >
            <span className="sdr-health-score__value">{readyCount}/{total}</span>
          </div>
          <div className="sdr-health-score__copy">
            <p className="sdr-health-score__title">Systems ready</p>
            <p className="sdr-health-score__desc">{pct}% integrations configured</p>
          </div>
          <span className={`sdr-health-score__pill ${pct === 100 ? 'sdr-health-score__pill--ok' : ''}`}>
            {pct === 100 ? 'All clear' : `${total - readyCount} pending`}
          </span>
        </div>

        <ul className="sdr-health-status-list">
          {readiness.map((item) => (
            <li key={item.label}>
              <div className={`sdr-health-status ${item.ok ? 'sdr-health-status--ok' : ''}`}>
                <span className="sdr-health-status__icon" aria-hidden>
                  {item.ok ? <CheckCircle2 className="h-4 w-4" /> : <CircleDashed className="h-4 w-4" />}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="sdr-health-status__row">
                    <p className="sdr-health-status__label">{item.label}</p>
                    <span className={`sdr-health-status__chip ${item.ok ? 'sdr-health-status__chip--ok' : ''}`}>
                      {item.ok ? 'Ready' : 'Action needed'}
                    </span>
                  </div>
                  <p className="sdr-health-status__detail">{item.ok ? 'Operational' : truncate(item.detail)}</p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="sdr-health-section">
        <header className="sdr-health-section__head">
          <h3 className="ws-heading-panel">Revenue operations</h3>
          <p className="ws-heading-panel-sub">Outbound, follow-up, and CRM pressure</p>
        </header>
        <div className="sdr-health-revenue-list">
          {revenue.map((item) => {
            const width = Math.max(Math.round((item.value / revenueMax) * 100), item.value > 0 ? 8 : 0)
            return (
              <div key={item.label} className="sdr-health-revenue-row">
                <div className="sdr-health-revenue-row__meta">
                  <span className="sdr-health-revenue-row__icon" aria-hidden>
                    <item.icon className="h-3.5 w-3.5" />
                  </span>
                  <span className="sdr-health-revenue-row__label">{item.label}</span>
                  <span className="sdr-health-revenue-row__value">{formatCount(item.value)}</span>
                </div>
                <div className="ws-funnel-track sdr-health-revenue-row__track" aria-hidden>
                  <div className="ws-funnel-fill sdr-health-revenue-row__fill" style={{ width: `${width}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      </section>

      <section className="sdr-health-section sdr-health-section--actions">
        <header className="sdr-health-section__head">
          <h3 className="ws-heading-panel">Quick actions</h3>
        </header>
        <nav className="sdr-health-actions" aria-label="Quick actions">
          {quickActions.map((action) => (
            <Link key={action.to} to={action.to} className="sdr-health-action group">
              <span>{action.label}</span>
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden />
            </Link>
          ))}
        </nav>
      </section>
    </div>
  )
}

export const healthRevenueIcons = {
  campaigns: Megaphone,
  meetings: CalendarClock,
  crm: RefreshCw,
  followUp: Mail,
} as const
