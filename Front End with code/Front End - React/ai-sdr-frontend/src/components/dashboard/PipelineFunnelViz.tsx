export type ChartStage = {
  label: string
  value: number
}

const CHART_W = 520
const ROW_H = 34
const BAR_H = 22
const PAD_TOP = 8

function formatCount(value: number) {
  return value.toLocaleString()
}

export function PipelineFunnelViz({ stages }: { stages: ChartStage[] }) {
  const peak = Math.max(...stages.map((s) => s.value), 1)
  const height = PAD_TOP + stages.length * ROW_H + 8

  return (
    <div className="sdr-funnel-viz" role="img" aria-label="Pipeline funnel chart">
      <svg
        viewBox={`0 0 ${CHART_W} ${height}`}
        className="sdr-funnel-viz__svg"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id="sdr-funnel-fill" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#18181b" />
            <stop offset="100%" stopColor="#52525b" />
          </linearGradient>
        </defs>
        {stages.map((stage, index) => {
          const y = PAD_TOP + index * ROW_H
          const widthRatio = stage.value / peak
          const barWidth = Math.max(widthRatio * (CHART_W - 120), stage.value > 0 ? 56 : 20)
          const x = (CHART_W - barWidth) / 2

          return (
            <g key={stage.label}>
              <text
                x={16}
                y={y + BAR_H - 6}
                className="sdr-funnel-viz__label"
              >
                {stage.label}
              </text>
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={BAR_H}
                rx={6}
                className="sdr-funnel-viz__bar"
                fill={stage.value > 0 ? 'url(#sdr-funnel-fill)' : 'var(--sdr-chart-track)'}
              />
              <text x={CHART_W - 16} y={y + BAR_H - 6} textAnchor="end" className="sdr-funnel-viz__value">
                {formatCount(stage.value)}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
