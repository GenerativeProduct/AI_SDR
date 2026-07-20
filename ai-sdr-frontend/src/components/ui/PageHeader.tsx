import { cn } from '../../lib/utils'
import { StatValue } from './StatValue'

export function PageHeader({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow?: string
  title?: string
  description?: string
  children?: React.ReactNode
}) {
  if (!eyebrow && !title && !description && !children) return null
  return (
    <header className="mb-4 flex flex-wrap items-end justify-between gap-3 border-b border-[var(--ws-border)] bg-white px-5 py-5">
      <div className="min-w-0">
        {eyebrow ? <p className="ws-eyebrow">{eyebrow}</p> : null}
        {title ? <h1 className={cn('ws-page-title', eyebrow ? 'mt-1' : undefined)}>{title}</h1> : null}
        {description ? <p className="ws-page-description">{description}</p> : null}
      </div>
      {children ? <div className="flex flex-wrap items-center gap-2">{children}</div> : null}
    </header>
  )
}

export function MetricCard({
  label,
  value,
  className,
}: {
  label: string
  value: string | number
  className?: string
}) {
  return (
    <div
      className={cn(
        'flex min-w-0 flex-col border-r border-[var(--ws-border)] bg-white p-4 transition-colors duration-200 last:border-r-0 hover:bg-zinc-50',
        className,
      )}
    >
      <p className="text-2xs font-medium uppercase tracking-wide text-[var(--ws-text-caption)]">{label}</p>
      <div className="mt-2">
        <StatValue>{value}</StatValue>
      </div>
    </div>
  )
}

export function MetricBar({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        'overflow-hidden rounded-xl border border-[var(--ws-border)] bg-white divide-y divide-[var(--ws-border)] sm:divide-x sm:divide-y-0',
        'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4',
        className,
      )}
    >
      {children}
    </div>
  )
}

export function StageCard({
  title,
  children,
  defaultOpen = false,
}: {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  return (
    <details
      className="rounded-xl border border-[var(--ws-border)] bg-white"
      open={defaultOpen}
    >
      <summary className="cursor-pointer list-none px-4 py-3 font-medium text-[var(--ws-text-primary)] marker:content-none">
        {title}
      </summary>
      <div className="border-t border-[var(--ws-border)] px-4 py-4 text-sm text-[var(--ws-text-secondary)]">
        {children}
      </div>
    </details>
  )
}

export function EmptyState({ message }: { message: string }) {
  return <div className="rounded-xl border border-dashed border-[var(--ws-border)] bg-zinc-50 px-4 py-10 text-center text-[var(--ws-text-caption)]">{message}</div>
}

export { Button } from './Button'
