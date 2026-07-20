import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

type CardSize = 'sm' | 'md'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean
  flat?: boolean
  size?: CardSize
}

const padding: Record<CardSize, string> = {
  sm: 'p-3',
  md: 'p-5',
}

export function Card({ hover, flat, size = 'md', className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'border border-[var(--ws-border)] bg-white shadow-[0_1px_2px_rgba(0,0,0,0.04)]',
        flat ? 'rounded-lg' : 'rounded-xl',
        padding[size],
        flat &&
          hover &&
          'cursor-pointer transition-colors duration-150 hover:border-zinc-300 hover:bg-zinc-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black/10',
        !flat &&
          hover &&
          'cursor-pointer transition-all duration-200 hover:-translate-y-px hover:border-zinc-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black/10',
        className,
      )}
      tabIndex={hover ? 0 : undefined}
      {...props}
    >
      {children}
    </div>
  )
}
