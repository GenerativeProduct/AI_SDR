import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { cn } from '../../lib/utils'
import { useUiStore } from '../../stores/uiStore'
import { CommandPalette } from './CommandPalette'
import { DesktopChrome } from './DesktopChrome'
import { MobileDrawer } from './MobileDrawer'
import { MobileNav } from './MobileNav'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

export function AppLayout() {
  const setCommandPaletteOpen = useUiStore((s) => s.setCommandPaletteOpen)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setCommandPaletteOpen(true)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [setCommandPaletteOpen])

  return (
    <div className="surface-workspace-shell flex min-h-svh max-h-svh overflow-hidden">
      <a
        href="#main-content"
        className="skip-to-main"
      >
        Skip to main content
      </a>
      <DesktopChrome />
      <Sidebar />
      <MobileDrawer />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden pb-16 md:pb-0">
        <div className="shrink-0 md:hidden">
          <TopBar />
        </div>
        <main
          id="main-content"
          tabIndex={-1}
          className={cn(
            'flex min-h-0 w-full flex-1 flex-col overflow-y-auto overflow-x-hidden outline-none',
            'md:pt-[var(--ws-topbar-height)]',
          )}
        >
          <div className="flex h-full min-h-0 w-full flex-1 flex-col">
            <Outlet />
          </div>
        </main>
      </div>
      <MobileNav />
      <CommandPalette />
    </div>
  )
}
