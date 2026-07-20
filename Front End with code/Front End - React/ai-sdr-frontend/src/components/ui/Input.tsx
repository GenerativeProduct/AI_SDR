import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from 'react'
import { cn } from '../../lib/utils'

type InputControlSize = 'sm' | 'md'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  leftIcon?: ReactNode
  error?: string
  inputSize?: InputControlSize
}

const inputSizes: Record<InputControlSize, string> = {
  sm: 'h-10 py-1.5',
  md: 'h-10 py-2',
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, label, leftIcon, error, inputSize = 'md', id: idProp, ...props },
  ref,
) {
  const generatedId = useId()
  const inputId = idProp ?? generatedId
  const errorId = `${inputId}-error`

  const field = (
    <div className="relative">
      {leftIcon && (
        <span
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-subtle"
          aria-hidden
        >
          {leftIcon}
        </span>
      )}
      <input
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'w-full rounded-lg border border-border-default bg-subtle px-3 text-sm text-text-primary',
          inputSizes[inputSize],
          'placeholder:text-text-subtle transition-colors duration-150',
          'hover:border-border-strong focus-ring',
          'disabled:cursor-not-allowed disabled:bg-overlay disabled:text-text-subtle disabled:opacity-60',
          error && 'border-danger focus-visible:border-danger',
          leftIcon && 'pl-9',
          className,
        )}
        {...props}
      />
    </div>
  )

  if (!label) {
    return (
      <div className="w-full">
        {field}
        {error ? (
          <p id={errorId} className="mt-1.5 text-xs text-danger" role="alert">
            {error}
          </p>
        ) : null}
      </div>
    )
  }

  return (
    <label className="block w-full text-sm text-text-secondary">
      {label}
      <div className="mt-1.5">{field}</div>
      {error ? (
        <p id={errorId} className="mt-1.5 text-xs text-danger" role="alert">
          {error}
        </p>
      ) : null}
    </label>
  )
})
