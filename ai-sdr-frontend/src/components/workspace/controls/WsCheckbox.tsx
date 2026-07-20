import { Check } from 'lucide-react'
import { cn } from '../../../lib/cn'

type WsCheckboxProps = {
  id?: string
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
  description?: string
  disabled?: boolean
  className?: string
}

export function WsCheckbox({
  id,
  checked,
  onChange,
  label,
  description,
  disabled,
  className,
}: WsCheckboxProps) {
  return (
    <label className={cn('ws-control-check', disabled && 'ws-control-check--disabled', className)}>
      <input
        id={id}
        type="checkbox"
        className="ws-control-check__native"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span className={cn('ws-control-check__box', checked && 'ws-control-check__box--checked')} aria-hidden>
        {checked ? <Check className="h-3 w-3" strokeWidth={3} /> : null}
      </span>
      <span className="ws-control-check__copy">
        <span className="ws-control-check__label">{label}</span>
        {description ? <span className="ws-control-check__desc">{description}</span> : null}
      </span>
    </label>
  )
}
