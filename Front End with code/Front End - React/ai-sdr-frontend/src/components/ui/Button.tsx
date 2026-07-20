import { Loader2 } from 'lucide-react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/utils'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'xs' | 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  leftIcon?: ReactNode
}

const variants: Record<Variant, string> = {
  primary:
    'bg-accent text-text-inverse hover:bg-accent-hover shadow-sm focus-visible:shadow-accent dark:shadow-none',
  secondary:
    'border border-border-default bg-surface text-text-secondary hover:border-border-strong hover:bg-overlay hover:text-text-primary dark:bg-raised dark:hover:bg-overlay',
  ghost:
    'text-text-secondary hover:bg-overlay hover:text-text-primary dark:hover:bg-overlay',
  danger:
    'bg-danger-muted text-danger-foreground border border-danger/20 hover:bg-danger hover:text-text-inverse',
}

const sizes: Record<Size, string> = {
  xs: 'h-8 px-3 text-xs gap-1',
  sm: 'h-10 px-3.5 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-11 px-5 text-base gap-2',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-lg font-medium tracking-tight transition-all duration-150',
        'focus-ring disabled:opacity-40 disabled:cursor-not-allowed',
        'active:scale-[var(--press-scale)]',
        loading && 'pointer-events-none opacity-70',
        variants[variant],
        sizes[size],
        className,
      )}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden />
      ) : (
        leftIcon
      )}
      {children}
    </button>
  )
}
