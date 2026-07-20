import { useState } from 'react'

export type FunnelStage = {
  label: string
  value: number
}

function formatCount(value: number) {
  return value.toLocaleString()
}

export function ConversionFunnelChart({ stages }: { stages: FunnelStage[] }) {
  const [active, setActive] = useState<number | null>(null)
  const peak = Math.max(...stages.map((s) => s.value), 1)
  const total = stages.reduce((sum, s) => sum + s.value, 0)
  const hasData = total > 0

  return (
    <div className="sdr-conversion-chart">
      <div className="sdr-conversion-chart__legend">
        <span>Stage</span>
        <span>Volume vs peak</span>
        <span>Count</span>
      </div>

      <ul className="sdr-conversion-chart__rows">
        {stages.map((stage, index) => {
          const width = Math.round((stage.value / peak) * 100)
          const prior = index > 0 ? stages[index - 1].value : null
          const conversion =
            prior !== null && prior > 0 ? Math.round((stage.value / prior) * 100) : null
          const isActive = active === index

          return (
            <li key={stage.label}>
              <button
                type="button"
                className={`sdr-conversion-row ${isActive ? 'sdr-conversion-row--active' : ''}`}
                onMouseEnter={() => setActive(index)}
                onMouseLeave={() => setActive(null)}
                onFocus={() => setActive(index)}
                onBlur={() => setActive(null)}
              >
                <span className="sdr-conversion-row__label">{stage.label}</span>
                <span className="sdr-conversion-row__track" aria-hidden>
                  <span
                    className="sdr-conversion-row__fill"
                    style={{ width: `${Math.max(width, stage.value > 0 ? 8 : 0)}%` }}
                  />
                </span>
                <span className="sdr-conversion-row__value">{formatCount(stage.value)}</span>
                {isActive ? (
                  <span className="sdr-conversion-row__tip" role="tooltip">
                    {stage.label}: {formatCount(stage.value)} ({width}% of peak)
                    {conversion !== null ? ` · ${conversion}% from prior` : ''}
                  </span>
                ) : null}
              </button>
            </li>
          )
        })}
      </ul>

      {!hasData ? (
        <p className="sdr-conversion-chart__empty">
          No pipeline volume yet. Run discovery or save an ICP to populate this funnel.
        </p>
      ) : (
        <p className="sdr-conversion-chart__footnote">
          Bar width shows each stage relative to the highest stage ({formatCount(peak)}).
        </p>
      )}
    </div>
  )
}
