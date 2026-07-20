import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

type PageHeaderProps = {
  eyebrow?: string
  title: string
  description?: string
  actions?: ReactNode
  className?: string
  embedded?: boolean
  /** Full-bleed flat header — no rounded card chrome (dashboard shell) */
  flush?: boolean
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
  embedded = false,
  flush = false,
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        'ws-page-header mb-4 flex flex-wrap items-end justify-between gap-3',
        embedded &&
          !flush &&
          '!mt-0 !mx-0 rounded-xl border border-[var(--ws-border)]',
        embedded &&
          flush &&
          '!mt-0 !mx-0 rounded-none border-0 border-b border-[var(--ws-border)]',
        className,
      )}
    >
      <div className="min-w-0">
        {eyebrow ? <p className="ws-eyebrow">{eyebrow}</p> : null}
        <h1 className={cn('ws-page-title', eyebrow ? 'mt-1' : undefined)}>{title}</h1>
        {description ? <p className="ws-page-description">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  )
}
