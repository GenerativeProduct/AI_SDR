import type { ReactNode } from 'react'
import { ChevronRight, LogOut, Moon, Search, Sun } from 'lucide-react'
import { useHealth } from '../../api/hooks'
import type { UserRole } from '../../api/types'
import { useLocation } from 'react-router-dom'
import { api, clearTokens } from '../../api/client'
import { getPageContext } from '../../config/navigation'
import { useAuthStore } from '../../stores/authStore'
import { useUiStore } from '../../stores/uiStore'
import { cn } from '../../lib/utils'

const ROLE_LABELS: Record<UserRole, string> = {
  operator: 'Operator',
  manager: 'Manager',
  admin: 'Admin',
}

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) {
    return `${parts[0][0] ?? ''}${parts[parts.length - 1][0] ?? ''}`.toUpperCase()
  }
  return (parts[0]?.slice(0, 2) ?? 'SD').toUpperCase()
}

function HealthBadge() {
  const health = useHealth()
  const ok = health.data?.status === 'ok'

  return (
    <span
      className={cn('ws-topbar-status-pill', ok ? 'ws-topbar-status-pill--ok' : 'ws-topbar-status-pill--warn')}
      title={ok ? 'API is reachable' : 'API is unreachable'}
    >
      <span className={cn('ws-topbar-status-pill__dot', ok && 'ws-topbar-status-pill__dot--pulse')} aria-hidden />
      <span className="hidden sm:inline">{ok ? 'Online' : 'Offline'}</span>
    </span>
  )
}

function TopBarIconButton({
  label,
  onClick,
  children,
  className,
}: {
  label: string
  onClick: () => void
  children: ReactNode
  className?: string
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      className={cn('ws-topbar-icon-btn ws-focus-ring', className)}
    >
      {children}
    </button>
  )
}

interface TopBarProps {
  embedded?: boolean
}

export function TopBar({ embedded = false }: TopBarProps) {
  const { pathname } = useLocation()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const setCommandPaletteOpen = useUiStore((s) => s.setCommandPaletteOpen)
  const theme = useUiStore((s) => s.theme)
  const toggleTheme = useUiStore((s) => s.toggleTheme)
  const { section, title, icon: PageIcon } = getPageContext(pathname)
  const displayName = user?.display_name ?? 'AI SDR'
  const roleLabel = user ? ROLE_LABELS[user.role] : 'Workspace'

  const handleLogout = async () => {
    try {
      const refresh = localStorage.getItem('sdr_refresh_token')
      await api.post('/auth/logout', { refresh_token: refresh })
    } catch {
      /* ignore */
    }
    clearTokens()
    logout()
    window.location.href = '/login'
  }

  const openPalette = () => setCommandPaletteOpen(true)

  return (
    <header
      className={cn(
        'surface-workspace-topbar ws-topbar',
        embedded && 'ws-topbar--embedded',
        embedded
          ? 'h-[var(--ws-topbar-height)]'
          : 'sticky top-0 z-30 h-[var(--ws-topbar-height)] shrink-0',
      )}
    >
      <div className="ws-topbar-context">
        <span className="ws-topbar-context__icon" aria-hidden>
          <PageIcon className="h-4 w-4" />
        </span>
        <div className="ws-topbar-context__copy min-w-0">
          <span className={cn('ws-topbar-eyebrow', !embedded && 'hidden sm:inline')}>{section}</span>
          <div className="ws-topbar-title-row">
            {embedded ? (
              <>
                <span className="ws-topbar-eyebrow ws-topbar-eyebrow--inline hidden lg:inline">{section}</span>
                <ChevronRight className="ws-topbar-chevron hidden lg:block" aria-hidden />
              </>
            ) : null}
            <h1 className="ws-topbar-title">{title}</h1>
          </div>
        </div>
      </div>

      {embedded ? (
        <div className="ws-topbar-search-wrap">
          <button type="button" onClick={openPalette} className="ws-topbar-search ws-focus-ring">
            <Search className="ws-topbar-search__icon h-4 w-4" aria-hidden />
            <span className="ws-topbar-search__placeholder">Search modules, agents, records…</span>
            <kbd className="ws-topbar-search__shortcut hidden md:inline-flex">⌘K</kbd>
          </button>
        </div>
      ) : null}

      <div className="ws-topbar-actions">
        {!embedded ? (
          <TopBarIconButton label="Open command palette" onClick={openPalette}>
            <Search className="h-4 w-4" />
          </TopBarIconButton>
        ) : null}
        <div className="ws-topbar-action-group">
          <HealthBadge />
          <TopBarIconButton
            label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
            onClick={toggleTheme}
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </TopBarIconButton>
        </div>

        <span className="ws-topbar-divider" aria-hidden />

        <div className="ws-topbar-action-group ws-topbar-action-group--identity">
          <div className="ws-topbar-user-chip hidden sm:inline-flex" title={`${displayName} · ${roleLabel}`}>
            <span className="ws-topbar-user-chip__avatar" aria-hidden>
              {initials(displayName)}
            </span>
            <span className="ws-topbar-user-chip__meta hidden md:flex">
              <span className="ws-topbar-user-chip__name">{displayName}</span>
              <span className="ws-topbar-user-chip__role">{roleLabel}</span>
            </span>
          </div>
          <TopBarIconButton label="Sign out" onClick={handleLogout} className="ws-topbar-signout">
            <LogOut className="h-4 w-4" />
            <span className="hidden xl:inline">Sign out</span>
          </TopBarIconButton>
        </div>
      </div>
    </header>
  )
}
