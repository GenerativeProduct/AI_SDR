type ReadinessItem = {
  label: string
  ok: boolean
}

export function ReadinessRing({ items }: { items: ReadinessItem[] }) {
  const ready = items.filter((item) => item.ok).length
  const total = Math.max(items.length, 1)
  const pct = ready / total
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - pct)

  return (
    <div className="sdr-readiness-ring">
      <svg viewBox="0 0 140 140" className="sdr-readiness-ring__svg" aria-hidden>
        <circle
          cx="70"
          cy="70"
          r={radius}
          className="sdr-readiness-ring__track"
          strokeWidth="10"
          fill="none"
        />
        <circle
          cx="70"
          cy="70"
          r={radius}
          className="sdr-readiness-ring__fill"
          strokeWidth="10"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
        />
      </svg>
      <div className="sdr-readiness-ring__center">
        <p className="sdr-readiness-ring__value">{ready}/{total}</p>
        <p className="sdr-readiness-ring__label">Systems ready</p>
      </div>
    </div>
  )
}
