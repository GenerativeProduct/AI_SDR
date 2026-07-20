import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react'
import { cn } from '../../../lib/cn'

type WsInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> & {
  inputSize?: 'sm' | 'md' | 'lg'
  leftSlot?: ReactNode
  rightSlot?: ReactNode
  invalid?: boolean
}

export const WsInput = forwardRef<HTMLInputElement, WsInputProps>(function WsInput(
  { className, inputSize = 'md', leftSlot, rightSlot, invalid, disabled, ...props },
  ref,
) {
  return (
    <div
      className={cn(
        'ws-control-input-wrap',
        `ws-control-input-wrap--${inputSize}`,
        leftSlot && 'ws-control-input-wrap--has-left',
        rightSlot && 'ws-control-input-wrap--has-right',
        invalid && 'ws-control-input-wrap--invalid',
        disabled && 'ws-control-input-wrap--disabled',
        className,
      )}
    >
      {leftSlot ? <span className="ws-control-input-wrap__slot ws-control-input-wrap__slot--left">{leftSlot}</span> : null}
      <input
        ref={ref}
        disabled={disabled}
        aria-invalid={invalid || undefined}
        className="ws-control-input"
        {...props}
      />
      {rightSlot ? <span className="ws-control-input-wrap__slot ws-control-input-wrap__slot--right">{rightSlot}</span> : null}
    </div>
  )
})
