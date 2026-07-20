import { ArrowRight, CalendarClock, Mail, Target, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '../../lib/utils'
import type { ProspectIntelligenceResult } from '../../api/types'
import { bandTone, formatPct, levelTone } from './intelligenceUtils'

type IntelligenceDetailPanelProps = {
  row: ProspectIntelligenceResult
}

function ProbabilityBar({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: number
  icon: typeof Mail
}) {
  const width = Math.min(100, Math.max(value > 0 ? 6 : 0, Math.round(value * 100)))

  return (
    <div className="sdr-intelligence__prob-row">
      <div className="sdr-intelligence__prob-row__meta">
        <span className="sdr-intelligence__prob-row__icon" aria-hidden>
          <Icon className="h-3.5 w-3.5" />
        </span>
        <span className="sdr-intelligence__prob-row__label">{label}</span>
        <span className="sdr-intelligence__prob-row__value">{formatPct(value)}</span>
      </div>
      <div className="ws-funnel-track sdr-intelligence__prob-row__track" aria-hidden>
        <div className="ws-funnel-fill sdr-intelligence__prob-row__fill" style={{ width: `${width}%` }} />
      </div>
    </div>
  )
}

export function IntelligenceDetailPanel({ row }: IntelligenceDetailPanelProps) {
  const intentTone = levelTone(row.intent.level)

  return (
    <aside className="sdr-intelligence__detail">
      <header className="sdr-intelligence__detail-header">
        <div>
          <p className="ws-heading-section">Scoring</p>
          <h2 className="sdr-intelligence__pane-title">
            {row.contact_name} @ {row.company_name}
          </h2>
          <p className="sdr-intelligence__pane-desc">{row.intent.recommended_timing}</p>
        </div>
        <span className={cn('sdr-intelligence__band-pill', `sdr-intelligence__band-pill--${bandTone(row.ranking.priority_band)}`)}>
          {row.ranking.priority_band} priority
        </span>
      </header>

      <div className="sdr-intelligence__detail-body">
        <div className="sdr-intelligence__score-card">
          <span className="sdr-intelligence__score-card__value">{row.ranking.priority_score.toFixed(1)}</span>
          <span className="sdr-intelligence__score-card__label">Priority score</span>
        </div>

        <section className="sdr-intelligence__detail-section">
          <h3 className="sdr-intelligence__detail-section__title">
            <TrendingUp className="h-4 w-4" aria-hidden />
            Intent assessment
          </h3>
          <div className="sdr-intelligence__intent-card">
            <div className="sdr-intelligence__intent-card__head">
              <span className={cn('sdr-intelligence__intent-pill', `sdr-intelligence__intent-pill--${intentTone}`)}>
                {row.intent.level} intent
              </span>
              <span className="sdr-intelligence__intent-card__pct">{formatPct(row.intent.probability.value)}</span>
            </div>
            <p className="sdr-intelligence__intent-card__timing">
              <CalendarClock className="h-3.5 w-3.5" aria-hidden />
              {row.intent.recommended_timing}
            </p>
          </div>
        </section>

        <section className="sdr-intelligence__detail-section">
          <h3 className="sdr-intelligence__detail-section__title">
            <Target className="h-4 w-4" aria-hidden />
            Propensity
          </h3>
          <div className="sdr-intelligence__prob-list">
            <ProbabilityBar label="Reply probability" value={row.propensity.reply_probability.value} icon={Mail} />
            <ProbabilityBar label="Meeting probability" value={row.propensity.meeting_probability.value} icon={CalendarClock} />
            <ProbabilityBar
              label="Qualification probability"
              value={row.propensity.qualification_probability.value}
              icon={Target}
            />
          </div>
        </section>

        {row.ranking.reasons?.length ? (
          <section className="sdr-intelligence__detail-section">
            <h3 className="sdr-intelligence__detail-section__title">Ranking rationale</h3>
            <ul className="sdr-intelligence__bullet-list">
              {row.ranking.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </section>
        ) : null}

        <div className="sdr-intelligence__detail-actions">
          <Link to="/qualification" className="ws-btn ws-btn--secondary w-full">
            Open qualification
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
          <Link to="/outreach" className="ws-btn ws-btn--primary w-full">
            Create outreach
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </div>
      </div>
    </aside>
  )
}
