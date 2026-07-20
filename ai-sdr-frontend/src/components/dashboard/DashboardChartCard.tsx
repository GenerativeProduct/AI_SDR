import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

type DashboardChartCardProps = {
  title: string
  description?: string
  children: ReactNode
  href?: string
  linkLabel?: string
  footer?: ReactNode
}

export function DashboardChartCard({
  title,
  description,
  children,
  href,
  linkLabel = 'View details',
  footer,
}: DashboardChartCardProps) {
  return (
    <section className="sdr-chart-card group">
      <header className="sdr-chart-card__header">
        <div className="min-w-0">
          <h3 className="sdr-chart-card__title">{title}</h3>
          {description ? <p className="sdr-chart-card__desc">{description}</p> : null}
        </div>
        {href ? (
          <Link to={href} className="sdr-chart-card__cta">
            <span>{linkLabel}</span>
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden />
          </Link>
        ) : null}
      </header>
      <div className="sdr-chart-card__body">{children}</div>
      {footer ? <footer className="sdr-chart-card__footer">{footer}</footer> : null}
    </section>
  )
}
