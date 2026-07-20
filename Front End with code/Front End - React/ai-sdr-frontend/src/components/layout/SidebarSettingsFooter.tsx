import { NavLink } from 'react-router-dom'
import { settingsNav } from '../../config/navigation'
import { sidebarNavClass, sidebarNavIconClass } from './sidebarNavStyles'

interface SidebarSettingsFooterProps {
  collapsed: boolean
  iconSize: string
  onNavigate?: () => void
  className?: string
}

export function SidebarSettingsFooter({
  collapsed,
  iconSize,
  onNavigate,
  className = 'ws-sidebar-footer',
}: SidebarSettingsFooterProps) {
  return (
    <div className={className}>
      <NavLink
        to={settingsNav.path}
        title={collapsed ? settingsNav.label : undefined}
        onClick={onNavigate}
        className={({ isActive }) =>
          collapsed
            ? sidebarNavClass(isActive, collapsed)
            : 'ws-sidebar-footer__link ws-focus-ring'
        }
      >
        {({ isActive }) => (
          <>
            <settingsNav.icon
              className={collapsed ? sidebarNavIconClass(isActive, iconSize) : 'ws-sidebar-footer__icon'}
              strokeWidth={1.75}
            />
            {!collapsed && <span>{settingsNav.label}</span>}
          </>
        )}
      </NavLink>
    </div>
  )
}
