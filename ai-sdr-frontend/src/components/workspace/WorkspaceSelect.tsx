import { useEffect, useId, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from 'react'
import { Check, ChevronDown } from 'lucide-react'
import { cn } from '../../lib/cn'
import { Icon } from '../ui/Icon'

export type WorkspaceSelectOption<T extends string = string> = {
  value: T
  label: string
}

type WorkspaceSelectProps<T extends string> = {
  id: string
  label?: string
  value: T
  options: WorkspaceSelectOption<T>[]
  onChange: (value: T) => void
  disabled?: boolean
  placeholder?: string
  className?: string
  'aria-label'?: string
}

export function WorkspaceSelect<T extends string>({
  id,
  label,
  value,
  options,
  onChange,
  disabled = false,
  placeholder = 'Select…',
  className,
  'aria-label': ariaLabel,
}: WorkspaceSelectProps<T>) {
  const listboxId = useId()
  const rootRef = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [highlightIndex, setHighlightIndex] = useState(0)

  const selected = options.find((opt) => opt.value === value)
  const displayLabel = selected?.label ?? placeholder

  useEffect(() => {
    if (!open) return
    const index = Math.max(0, options.findIndex((opt) => opt.value === value))
    setHighlightIndex(index)
  }, [open, options, value])

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  const selectIndex = (index: number) => {
    const option = options[index]
    if (!option) return
    onChange(option.value)
    setOpen(false)
  }

  const onTriggerKeyDown = (event: ReactKeyboardEvent<HTMLButtonElement>) => {
    if (disabled) return
    if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      setOpen(true)
      return
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault()
      setOpen(true)
      setHighlightIndex(options.length - 1)
    }
  }

  const onListKeyDown = (event: ReactKeyboardEvent<HTMLUListElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setHighlightIndex((i) => Math.min(options.length - 1, i + 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setHighlightIndex((i) => Math.max(0, i - 1))
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      selectIndex(highlightIndex)
    } else if (event.key === 'Escape') {
      event.preventDefault()
      setOpen(false)
    } else if (event.key === 'Home') {
      event.preventDefault()
      setHighlightIndex(0)
    } else if (event.key === 'End') {
      event.preventDefault()
      setHighlightIndex(options.length - 1)
    }
  }

  return (
    <div ref={rootRef} className={cn('ws-select', className)}>
      {label ? (
        <label className="ws-select__label" htmlFor={id}>
          {label}
        </label>
      ) : null}
      <button
        id={id}
        type="button"
        disabled={disabled}
        aria-label={label ? undefined : ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        className={cn('ws-select__trigger ws-focus-ring', open && 'ws-select__trigger--open')}
        onClick={() => !disabled && setOpen((v) => !v)}
        onKeyDown={onTriggerKeyDown}
      >
        <span className={cn('ws-select__value', !selected && 'ws-select__value--placeholder')}>
          {displayLabel}
        </span>
        <Icon
          icon={ChevronDown}
          size="sm"
          className={cn('ws-select__chevron', open && 'ws-select__chevron--open')}
        />
      </button>
      {open ? (
        <ul
          id={listboxId}
          role="listbox"
          aria-labelledby={label ? id : undefined}
          aria-label={label ? undefined : ariaLabel}
          className="ws-select__menu"
          onKeyDown={onListKeyDown}
        >
          {options.map((option, index) => {
            const isSelected = option.value === value
            const isHighlighted = index === highlightIndex
            return (
              <li key={option.value} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={cn(
                    'ws-select__option',
                    isSelected && 'ws-select__option--selected',
                    isHighlighted && 'ws-select__option--highlighted',
                  )}
                  onMouseEnter={() => setHighlightIndex(index)}
                  onClick={() => selectIndex(index)}
                >
                  <span className="ws-select__option-label">{option.label}</span>
                  {isSelected ? <Icon icon={Check} size="sm" className="ws-select__option-check" /> : null}
                </button>
              </li>
            )
          })}
        </ul>
      ) : null}
    </div>
  )
}
