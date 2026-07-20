type DashboardMetricBarProps = {
  label: string
  value: number
  max: number
  formatValue?: (value: number) => string
}

function defaultFormat(value: number) {
  return value.toLocaleString()
}

export function DashboardMetricBar({
  label,
  value,
  max,
  formatValue = defaultFormat,
}: DashboardMetricBarProps) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  const width = `${Math.max(pct, value > 0 ? 6 : 0)}%`

  return (
    <div className="sdr-dash-bar">
      <div className="sdr-dash-bar__labels">
        <span className="sdr-dash-bar__label">{label}</span>
        <span className="sdr-dash-bar__value">{formatValue(value)}</span>
      </div>
      <div className="ws-funnel-track sdr-dash-bar__track" aria-hidden>
        <div className="ws-funnel-fill sdr-dash-bar__fill" style={{ width }} />
      </div>
    </div>
  )
}

export function DashboardMetricBarList({
  items,
}: {
  items: Array<{ label: string; value: number }>
}) {
  const max = Math.max(1, ...items.map((item) => item.value))

  return (
    <div className="sdr-dash-bar-list">
      {items.map((item) => (
        <DashboardMetricBar key={item.label} label={item.label} value={item.value} max={max} />
      ))}
    </div>
  )
}
