import type { LucideIcon } from 'lucide-react'
import { cn } from '../../lib/utils'

export type SettingsSection = 'profile' | 'appearance' | 'api' | 'admin' | 'providers'

type NavItem = {
  id: SettingsSection
  label: string
  icon: LucideIcon
}

type SettingsNavPanelProps = {
  section: SettingsSection
  items: NavItem[]
  onSectionChange: (section: SettingsSection) => void
}

export function SettingsNavPanel({ section, items, onSectionChange }: SettingsNavPanelProps) {
  return (
    <aside className="sdr-split__left">
      <header className="sdr-split__left-header">
        <div>
          <p className="ws-heading-section">Sections</p>
          <h2 className="sdr-split__pane-title">Settings</h2>
          <p className="sdr-split__pane-desc">Workspace preferences and system configuration.</p>
        </div>
      </header>

      <nav className="sdr-split__left-body" aria-label="Settings sections">
        <div className="sdr-split__nav-list">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              className={cn('sdr-split__nav-item ws-focus-ring', section === item.id && 'sdr-split__nav-item--active')}
              onClick={() => onSectionChange(item.id)}
            >
              <item.icon className="h-4 w-4 shrink-0" aria-hidden />
              {item.label}
            </button>
          ))}
        </div>
      </nav>
    </aside>
  )
}
