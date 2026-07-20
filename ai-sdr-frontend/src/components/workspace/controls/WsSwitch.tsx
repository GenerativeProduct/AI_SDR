import { cn } from '../../../lib/cn'

type WsSwitchProps = {
  id?: string
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
  description?: string
  disabled?: boolean
  className?: string
}

export function WsSwitch({
  id,
  checked,
  onChange,
  label,
  description,
  disabled,
  className,
}: WsSwitchProps) {
  return (
    <div className={cn('ws-control-switch-row', className)}>
      <div className="ws-control-switch-row__copy">
        <span className="ws-control-switch-row__label" id={id ? `${id}-label` : undefined}>
          {label}
        </span>
        {description ? <span className="ws-control-switch-row__desc">{description}</span> : null}
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        aria-labelledby={id ? `${id}-label` : undefined}
        disabled={disabled}
        className={cn('ws-control-switch ws-focus-ring', checked && 'ws-control-switch--on')}
        onClick={() => onChange(!checked)}
      >
        <span className="ws-control-switch__thumb" aria-hidden />
      </button>
    </div>
  )
}
