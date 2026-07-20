import { useState } from 'react'

export type StageBarDatum = {
  label: string
  value: number
}

function formatCount(value: number) {
  return value.toLocaleString()
}

export function StageVolumeChart({ data }: { data: StageBarDatum[] }) {
  const [active, setActive] = useState<number | null>(null)
  const max = Math.max(1, ...data.map((d) => d.value))
  const ticks = [0, Math.ceil(max / 2), max]

  return (
    <div className="sdr-volume-chart">
      <div className="sdr-volume-chart__plot">
        <div className="sdr-volume-chart__y-axis" aria-hidden>
          {ticks
            .slice()
            .reverse()
            .map((tick) => (
              <span key={tick} className="sdr-volume-chart__tick">
                {formatCount(tick)}
              </span>
            ))}
        </div>

        <div className="sdr-volume-chart__canvas">
          <div className="sdr-volume-chart__grid" aria-hidden>
            {ticks.map((tick) => (
              <div key={tick} className="sdr-volume-chart__gridline" />
            ))}
          </div>

          <ul className="sdr-volume-chart__bars">
            {data.map((item, index) => {
              const height = Math.round((item.value / max) * 100)
              const isActive = active === index

              return (
                <li key={item.label}>
                  <button
                    type="button"
                    className={`sdr-volume-bar ${isActive ? 'sdr-volume-bar--active' : ''}`}
                    onMouseEnter={() => setActive(index)}
                    onMouseLeave={() => setActive(null)}
                    onFocus={() => setActive(index)}
                    onBlur={() => setActive(null)}
                  >
                    <span className="sdr-volume-bar__value">{formatCount(item.value)}</span>
                    <span className="sdr-volume-bar__track" aria-hidden>
                      <span
                        className="sdr-volume-bar__fill"
                        style={{ height: `${Math.max(height, item.value > 0 ? 10 : 2)}%` }}
                      />
                    </span>
                    <span className="sdr-volume-bar__label">{item.label}</span>
                    {isActive ? (
                      <span className="sdr-volume-bar__tip" role="tooltip">
                        {item.label}: {formatCount(item.value)}
                      </span>
                    ) : null}
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      </div>
    </div>
  )
}
