import { cn } from '../../lib/utils'

export function sidebarNavClass(isActive: boolean, collapsed: boolean) {
  return cn(
    'ws-sidebar-link ws-focus-ring',
    collapsed && 'justify-center px-0',
    isActive ? 'font-semibold' : undefined,
  )
}

export function sidebarNavIconClass(isActive: boolean, sizeClass: string) {
  return cn(
    sizeClass,
    'ws-sidebar-link__icon',
    isActive ? 'text-[var(--ws-text-primary)]' : undefined,
  )
}
