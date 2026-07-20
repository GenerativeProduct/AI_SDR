import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

type SplitPaneProps = {
  list: ReactNode
  detail: ReactNode
  listWidth?: string
  className?: string
  mobileShowDetail?: boolean
}

export function SplitPane({
  list,
  detail,
  listWidth = 'var(--ws-queue-width)',
  className,
  mobileShowDetail = false,
}: SplitPaneProps) {
  return (
    <div className={cn('flex min-h-0 flex-1 flex-col lg:flex-row', className)}>
      <div
        className={cn(
          'flex w-full shrink-0 flex-col border-b border-[var(--ws-border)] lg:w-auto lg:border-b-0 lg:border-r',
          mobileShowDetail && 'hidden lg:flex',
        )}
      >
        <div className="flex min-h-0 flex-1 flex-col lg:hidden">{list}</div>
        <div className="hidden min-h-0 flex-col lg:flex" style={{ width: listWidth }}>
          {list}
        </div>
      </div>
      <div
        className={cn('flex min-h-0 min-w-0 flex-1 flex-col', !mobileShowDetail && 'hidden lg:flex')}
      >
        {detail}
      </div>
    </div>
  )
}
