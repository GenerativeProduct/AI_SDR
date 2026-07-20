import { Search, X } from 'lucide-react'
import { WsInput } from './WsInput'

type WsSearchInputProps = {
  id?: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  'aria-label'?: string
  onClear?: () => void
}

export function WsSearchInput({
  id,
  value,
  onChange,
  placeholder = 'Search…',
  disabled,
  'aria-label': ariaLabel,
  onClear,
}: WsSearchInputProps) {
  return (
    <WsInput
      id={id}
      type="search"
      value={value}
      disabled={disabled}
      placeholder={placeholder}
      aria-label={ariaLabel}
      inputSize="md"
      leftSlot={<Search className="h-4 w-4" aria-hidden />}
      rightSlot={
        value ? (
          <button
            type="button"
            className="ws-control-clear-btn ws-focus-ring"
            aria-label="Clear search"
            onClick={() => {
              onChange('')
              onClear?.()
            }}
          >
            <X className="h-3.5 w-3.5" aria-hidden />
          </button>
        ) : null
      }
      onChange={(e) => onChange(e.target.value)}
    />
  )
}
