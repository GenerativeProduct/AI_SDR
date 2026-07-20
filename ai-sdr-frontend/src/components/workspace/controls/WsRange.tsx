import { cn } from '../../../lib/cn'

type WsRangeProps = {
  id?: string
  value: number
  min?: number
  max?: number
  step?: number
  onChange: (value: number) => void
  label?: string
  hint?: string
  formatValue?: (value: number) => string
  disabled?: boolean
  className?: string
}

export function WsRange({
  id,
  value,
  min = 0,
  max = 1,
  step = 0.05,
  onChange,
  label,
  hint,
  formatValue = (v) => `${Math.round(v * 100)}%`,
  disabled,
  className,
}: WsRangeProps) {
  const pct = ((value - min) / (max - min)) * 100

  return (
    <div className={cn('ws-control-range', className)}>
      {label || hint ? (
        <div className="ws-control-range__head">
          {label ? <span className="ws-control-range__label">{label}</span> : <span />}
          <span className="ws-control-range__value">{formatValue(value)}</span>
        </div>
      ) : null}
      {hint ? <p className="ws-control-range__hint">{hint}</p> : null}
      <div className="ws-control-range__shell">
        <div className="ws-control-range__track" aria-hidden>
          <span className="ws-control-range__fill" style={{ width: `${pct}%` }} />
        </div>
        <input
          id={id}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          disabled={disabled}
          aria-label={label}
          className="ws-control-range__input"
          onChange={(e) => onChange(Number(e.target.value))}
        />
      </div>
    </div>
  )
}
