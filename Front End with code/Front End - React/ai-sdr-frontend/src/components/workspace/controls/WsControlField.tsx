import type { ReactNode } from 'react'
import { cn } from '../../../lib/cn'

type WsControlFieldProps = {
  id?: string
  label?: string
  hint?: string
  error?: string
  children: ReactNode
  className?: string
  required?: boolean
}

export function WsControlField({
  id,
  label,
  hint,
  error,
  children,
  className,
  required,
}: WsControlFieldProps) {
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined
  const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined

  return (
    <div className={cn('ws-control-field', className)}>
      {label ? (
        <label className="ws-control-field__label" htmlFor={id}>
          {label}
          {required ? <span className="ws-control-field__required" aria-hidden> *</span> : null}
        </label>
      ) : null}
      <div className="ws-control-field__control" data-describedby={describedBy}>
        {children}
      </div>
      {hint && !error ? (
        <p id={hintId} className="ws-control-field__hint">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} className="ws-control-field__error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}
