import type { LucideIcon } from 'lucide-react'
import {
  BarChart3,
  Brain,
  Calendar,
  Compass,
  FlaskConical,
  LayoutDashboard,
  Mail,
  MessageSquare,
  Repeat,
  Search,
  Settings,
  Sparkles,
  Target,
  Users,
} from 'lucide-react'

export interface NavItem {
  path: string
  label: string
  icon: LucideIcon
}

export interface NavSection {
  title: string
  items: NavItem[]
}

export const navSections: NavSection[] = [
  {
    title: 'Overview',
    items: [
      { path: '/', label: 'Dashboard', icon: LayoutDashboard },
      { path: '/pipeline', label: 'Pipeline Chat', icon: Sparkles },
    ],
  },
  {
    title: 'Pipeline',
    items: [
      { path: '/icp', label: 'ICP', icon: Target },
      { path: '/discovery', label: 'Discovery', icon: Compass },
      { path: '/enrichment', label: 'Enrichment', icon: Search },
      { path: '/intelligence', label: 'Intelligence', icon: Brain },
      { path: '/qualification', label: 'Qualification', icon: FlaskConical },
    ],
  },
  {
    title: 'Operations',
    items: [
      { path: '/outreach', label: 'Outreach', icon: Mail },
      { path: '/conversations', label: 'Conversations', icon: MessageSquare },
      { path: '/follow-up', label: 'Follow-Up', icon: Repeat },
      { path: '/meetings', label: 'Meetings', icon: Calendar },
      { path: '/crm', label: 'CRM', icon: Users },
    ],
  },
  {
    title: 'Insights',
    items: [{ path: '/analytics', label: 'Analytics', icon: BarChart3 }],
  },
]

export const settingsNavItem: NavItem = {
  path: '/settings',
  label: 'Settings',
  icon: Settings,
}

export const settingsNav = settingsNavItem

export const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/pipeline': 'Pipeline Chat',
  '/icp': 'ICP Advanced',
  '/discovery': 'Discovery',
  '/enrichment': 'Enrichment',
  '/intelligence': 'Intelligence',
  '/qualification': 'Qualification',
  '/outreach': 'Outreach Inbox',
  '/conversations': 'Conversations',
  '/follow-up': 'Follow-Up',
  '/meetings': 'Meetings & CRM',
  '/crm': 'CRM',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
}

export interface PageContext {
  section: string
  title: string
  icon: LucideIcon
}

export function getPageContext(pathname: string): PageContext {
  for (const section of navSections) {
    const item = section.items.find((entry) => entry.path === pathname)
    if (item) {
      return {
        section: section.title,
        title: pageTitles[pathname] ?? item.label,
        icon: item.icon,
      }
    }
  }

  if (pathname === settingsNavItem.path) {
    return {
      section: 'System',
      title: pageTitles[pathname] ?? settingsNavItem.label,
      icon: settingsNavItem.icon,
    }
  }

  return {
    section: 'Workspace',
    title: pageTitles[pathname] ?? 'AI SDR',
    icon: LayoutDashboard,
  }
}
