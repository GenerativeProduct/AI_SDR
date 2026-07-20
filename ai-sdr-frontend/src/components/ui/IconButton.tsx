import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/utils'

type IconButtonVariant = 'ghost' | 'outline'
type IconButtonSize = 'sm' | 'md'

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string
  children: ReactNode
  variant?: IconButtonVariant
  size?: IconButtonSize
}

const sizes: Record<IconButtonSize, string> = {
  sm: 'h-8 w-8 rounded-lg',
  md: 'h-9 w-9 rounded-lg',
}

const variants: Record<IconButtonVariant, string> = {
  ghost:
    'text-text-tertiary hover:bg-overlay hover:text-text-primary border border-transparent',
  outline:
    'border border-border-default bg-surface text-text-tertiary hover:border-border-strong hover:bg-subtle hover:text-text-primary',
}

export function IconButton({
  label,
  children,
  variant = 'ghost',
  size = 'sm',
  className,
  type = 'button',
  title,
  ...props
}: IconButtonProps) {
  return (
    <button
      type={type}
      aria-label={label}
      title={title ?? label}
      className={cn(
        'inline-flex shrink-0 items-center justify-center transition-all duration-150',
        'active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/25 focus-visible:ring-offset-2 focus-visible:ring-offset-surface',
        'disabled:pointer-events-none disabled:opacity-40',
        sizes[size],
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
