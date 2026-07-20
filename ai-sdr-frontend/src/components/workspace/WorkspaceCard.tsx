import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Icon } from '../ui/Icon'
import { cn } from '../../lib/cn'

type WorkspaceCardProps = {
  title: string
  icon?: LucideIcon
  children: ReactNode
  className?: string
  action?: ReactNode
}

export function WorkspaceCard({ title, icon, children, className, action }: WorkspaceCardProps) {
  return (
    <article className={cn('ws-card', className)}>
      <div className="flex items-center justify-between gap-2">
        <h2 className="ws-section-title flex items-center gap-2">
          {icon ? <Icon icon={icon} size="sm" className="text-[var(--ws-text-muted)]" /> : null}
          {title}
        </h2>
        {action}
      </div>
      <div className="mt-3">{children}</div>
    </article>
  )
}
