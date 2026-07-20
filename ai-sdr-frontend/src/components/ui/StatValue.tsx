import type { ReactNode } from 'react'
import { cn } from '../../lib/utils'

export function StatValue({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <p className={cn('tabular-nums text-xl font-semibold tracking-tight text-text-primary', className)}>
      {children}
    </p>
  )
}
