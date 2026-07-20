interface FunnelStage {
  label: string
  value: number
}

export function FunnelChart({ stages }: { stages: FunnelStage[] }) {
  const max = Math.max(...stages.map((s) => s.value), 1)

  return (
    <div className="space-y-3">
      {stages.map((stage) => {
        const pct = Math.round((stage.value / max) * 100)
        return (
          <div key={stage.label}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="text-[var(--ws-text-secondary)]">{stage.label}</span>
              <span className="tabular-nums text-[var(--ws-text-muted)]">{stage.value}</span>
            </div>
            <div className="ws-funnel-track">
              <div
                className="ws-funnel-fill"
                style={{ width: `${Math.max(pct, stage.value > 0 ? 4 : 0)}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
