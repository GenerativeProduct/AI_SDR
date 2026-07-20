import type { ReactNode } from 'react'

export function PageLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full min-h-0 w-full flex-col overflow-hidden bg-[var(--ws-canvas)]">
      <div className="flex min-h-0 w-full flex-1 flex-col overflow-y-auto overscroll-y-contain">
        <div className="ws-panel-enter flex w-full flex-col gap-4 px-4 py-5 md:px-6 md:py-6">
          {children}
        </div>
      </div>
    </div>
  )
}
