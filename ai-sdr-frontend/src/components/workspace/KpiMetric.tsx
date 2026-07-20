type KpiMetricProps = {
  label: string
  value: string | number
  hint?: string
}

export function KpiMetric({ label, value, hint }: KpiMetricProps) {
  return (
    <article className="ws-kpi-tile">
      <p className="ws-kpi-tile__label">{label}</p>
      <p className="ws-kpi-tile__value">{value}</p>
      {hint ? <p className="mt-1 text-xs text-[var(--ws-text-muted)]">{hint}</p> : null}
    </article>
  )
}

export function KpiMetricGrid({
  children,
  columns = 6,
}: {
  children: React.ReactNode
  columns?: 3 | 6
}) {
  return (
    <div className={`ws-kpi-grid ${columns === 6 ? 'ws-kpi-grid--6' : ''}`}>{children}</div>
  )
}
