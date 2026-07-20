import { LayoutDashboard, LayoutGrid, Menu, Sparkles } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { IconButton } from '../ui/IconButton'
import { cn } from '../../lib/utils'
import { useUiStore } from '../../stores/uiStore'

const tabs = [
  { path: '/', icon: LayoutDashboard, label: 'Home' },
  { path: '/pipeline', icon: Sparkles, label: 'Pipeline' },
  { path: '/outreach', icon: LayoutGrid, label: 'Outreach' },
]

export function MobileNav() {
  const setMobileNavOpen = useUiStore((s) => s.setMobileNavOpen)

  return (
    <>
      <nav
        className="surface-workspace-mobile fixed bottom-0 left-0 right-0 z-40 flex border-t border-[var(--ws-border)] bg-[var(--ws-surface-raised,#fff)] pb-[env(safe-area-inset-bottom)] md:hidden"
        aria-label="Primary mobile"
      >
        {tabs.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            end={tab.path === '/'}
            className={({ isActive }) =>
              cn(
                'flex flex-1 flex-col items-center gap-1 py-2.5 text-2xs transition-all duration-150 active:scale-95',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-black/10',
                isActive ? 'text-[var(--ws-text-primary)]' : 'text-[var(--ws-text-caption)]',
              )
            }
          >
            <tab.icon className="h-[22px] w-[22px]" strokeWidth={1.75} />
            {tab.label}
          </NavLink>
        ))}
        <button
          type="button"
          aria-label="More navigation"
          onClick={() => setMobileNavOpen(true)}
          className={cn(
            'flex flex-1 flex-col items-center gap-1 py-2.5 text-2xs text-[var(--ws-text-caption)] transition-all duration-150 active:scale-95',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-black/10',
          )}
        >
          <Menu className="h-[22px] w-[22px]" strokeWidth={1.75} />
          More
        </button>
      </nav>

      <IconButton
        id="mobile-menu-trigger"
        label="Open menu"
        variant="outline"
        size="md"
        className="surface-workspace-mobile fixed left-4 top-4 z-50 bg-[var(--ws-surface-raised,#fff)] md:hidden"
        onClick={() => setMobileNavOpen(true)}
      >
        <Menu className="h-5 w-5" aria-hidden />
      </IconButton>
    </>
  )
}
