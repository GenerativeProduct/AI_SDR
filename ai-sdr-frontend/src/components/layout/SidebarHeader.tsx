import { ChevronLeft, ChevronRight, Sparkles } from 'lucide-react'
import { cn } from '../../lib/utils'
import { useUiStore } from '../../stores/uiStore'

export function SidebarHeader() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed)
  const toggleSidebar = useUiStore((s) => s.toggleSidebar)

  if (collapsed) {
    return (
      <div
        className={cn(
          'surface-workspace-sidebar hidden h-[var(--ws-topbar-height)] shrink-0 items-center justify-center border-r md:flex',
          'w-[72px] transition-[width] duration-200 ease-in-out',
        )}
      >
        <button
          type="button"
          aria-label="Expand sidebar"
          onClick={toggleSidebar}
          className="ws-btn ws-btn--ghost ws-btn--compact"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'surface-workspace-sidebar hidden h-[var(--ws-topbar-height)] shrink-0 items-center gap-2.5 border-r px-4 md:flex',
        'w-[var(--ws-sidebar-width)]',
        'transition-[width] duration-200 ease-in-out',
      )}
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-[var(--ws-border)] bg-zinc-50 text-[var(--ws-text-primary)]">
        <Sparkles className="h-[18px] w-[18px]" aria-hidden />
      </span>
      <span className="min-w-0 flex-1 truncate">
        <span className="block truncate text-sm font-semibold tracking-tight text-[var(--ws-text-primary)]">
          AI SDR
        </span>
        <span className="block truncate text-xs font-medium text-[var(--ws-text-caption)]">
          Revenue workspace
        </span>
      </span>
      <button
        type="button"
        aria-label="Collapse sidebar"
        onClick={toggleSidebar}
        className="ws-btn ws-btn--ghost ws-btn--compact"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
    </div>
  )
}
