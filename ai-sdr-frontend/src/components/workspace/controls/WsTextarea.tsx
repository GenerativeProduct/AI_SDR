import { forwardRef, type TextareaHTMLAttributes } from 'react'
import { cn } from '../../../lib/cn'

type WsTextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  invalid?: boolean
  resize?: 'none' | 'vertical' | 'both'
}

export const WsTextarea = forwardRef<HTMLTextAreaElement, WsTextareaProps>(function WsTextarea(
  { className, invalid, disabled, resize = 'vertical', rows = 4, ...props },
  ref,
) {
  return (
    <div
      className={cn(
        'ws-control-textarea-wrap',
        `ws-control-textarea-wrap--resize-${resize}`,
        invalid && 'ws-control-textarea-wrap--invalid',
        disabled && 'ws-control-textarea-wrap--disabled',
        className,
      )}
    >
      <textarea
        ref={ref}
        disabled={disabled}
        rows={rows}
        aria-invalid={invalid || undefined}
        className="ws-control-textarea"
        {...props}
      />
    </div>
  )
})
