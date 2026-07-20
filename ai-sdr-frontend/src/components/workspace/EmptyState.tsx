import type { ReactNode } from 'react'
import { Inbox } from 'lucide-react'

type EmptyStateProps = {
  title: string
  description?: string
  action?: ReactNode
  icon?: ReactNode
}

export function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center px-8 py-16 text-center ws-panel-enter">
      <div className="ws-empty-icon mb-4">
        {icon ?? <Inbox className="h-7 w-7" aria-hidden />}
      </div>
      <h2 className="text-xl font-semibold tracking-tight text-[var(--ws-text-primary)]">{title}</h2>
      {description ? (
        <p className="mt-2 max-w-sm text-sm text-[var(--ws-text-muted)]">{description}</p>
      ) : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  )
}
