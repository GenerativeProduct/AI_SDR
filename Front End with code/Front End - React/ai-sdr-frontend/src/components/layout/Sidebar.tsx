import { navSections } from '../../config/navigation'
import { cn } from '../../lib/utils'
import { useUiStore } from '../../stores/uiStore'
import { SidebarNavSections } from './SidebarNavSections'
import { SidebarSettingsFooter } from './SidebarSettingsFooter'

const iconSize = 'h-[22px] w-[22px]'

export function Sidebar() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed)

  return (
    <aside
      className={cn(
        'surface-workspace-sidebar hidden shrink-0 flex-col overflow-hidden border-r transition-[width] duration-200 ease-in-out md:flex md:pt-[var(--ws-topbar-height)]',
        collapsed ? 'w-[72px]' : 'w-[var(--ws-sidebar-width)]',
      )}
    >
      <nav
        aria-label="Main navigation"
        className="ws-sidebar flex flex-1 flex-col overflow-hidden"
      >
        <div className="ws-sidebar-scroll">
          <SidebarNavSections sections={navSections} collapsed={collapsed} iconSize={iconSize} />
        </div>
        <SidebarSettingsFooter collapsed={collapsed} iconSize={iconSize} className="ws-sidebar-footer" />
      </nav>
    </aside>
  )
}
