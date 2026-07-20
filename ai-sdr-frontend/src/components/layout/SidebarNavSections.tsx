import { NavLink } from 'react-router-dom'
import type { NavSection } from '../../config/navigation'
import { sidebarNavClass, sidebarNavIconClass } from './sidebarNavStyles'

interface SidebarNavSectionsProps {
  sections: NavSection[]
  collapsed: boolean
  iconSize: string
  onNavigate?: () => void
}

export function SidebarNavSections({
  sections,
  collapsed,
  iconSize,
  onNavigate,
}: SidebarNavSectionsProps) {
  return (
    <>
      {sections.map((section) => (
        <section key={section.title} className="ws-sidebar-section" aria-label={section.title}>
          {!collapsed ? <h2 className="ws-sidebar-section__label">{section.title}</h2> : null}
          <ul className="flex flex-col gap-0.5">
            {section.items.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  end={item.path === '/'}
                  title={collapsed ? item.label : undefined}
                  onClick={onNavigate}
                  className={({ isActive }) => sidebarNavClass(isActive, collapsed)}
                >
                  {({ isActive }) => (
                    <>
                      {isActive ? <span className="ws-sidebar-link__indicator" aria-hidden /> : null}
                      <item.icon className={sidebarNavIconClass(isActive, iconSize)} strokeWidth={1.75} />
                      {!collapsed && <span className="ws-sidebar-link__label">{item.label}</span>}
                    </>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </>
  )
}
