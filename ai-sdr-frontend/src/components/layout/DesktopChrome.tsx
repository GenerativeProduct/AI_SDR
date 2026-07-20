import { SidebarHeader } from './SidebarHeader'
import { TopBar } from './TopBar'

export function DesktopChrome() {
  return (
    <div className="fixed left-0 right-0 top-0 z-50 hidden h-[var(--ws-topbar-height)] md:flex">
      <SidebarHeader />
      <TopBar embedded />
    </div>
  )
}
