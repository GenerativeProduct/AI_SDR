import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

type DataTableProps = {
  children: ReactNode
  className?: string
  'aria-label'?: string
}

export function DataTable({ children, className, 'aria-label': ariaLabel }: DataTableProps) {
  return (
    <div
      role="grid"
      aria-label={ariaLabel ?? 'Data table'}
      className={cn('flex min-h-0 flex-1 flex-col overflow-hidden', className)}
    >
      {children}
    </div>
  )
}

export function DataTableBody({ children }: { children: ReactNode }) {
  return (
    <div role="rowgroup" className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
      {children}
    </div>
  )
}
