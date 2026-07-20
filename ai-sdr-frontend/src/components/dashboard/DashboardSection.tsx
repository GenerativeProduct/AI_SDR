import type { ReactNode } from 'react'
import { PageSectionTitle } from '../ui/PageSectionTitle'
import { cn } from '../../lib/utils'

export function DashboardSection({
  title,
  description,
  children,
  className,
}: {
  title: string
  description?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section className={cn('ws-card flex flex-col', className)}>
      <header className="mb-4 flex shrink-0 items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <PageSectionTitle as="h3" className="ws-section-title">{title}</PageSectionTitle>
          {description ? (
            <p className="mt-1.5 max-w-prose text-sm font-normal leading-relaxed text-[var(--ws-text-muted)]">
              {description}
            </p>
          ) : null}
        </div>
      </header>
      <div>{children}</div>
    </section>
  )
}
