import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { navSections } from '../../config/navigation'
import { IconButton } from '../ui/IconButton'
import { useUiStore } from '../../stores/uiStore'
import { SidebarNavSections } from './SidebarNavSections'
import { SidebarSettingsFooter } from './SidebarSettingsFooter'

export function MobileDrawer() {
  const open = useUiStore((s) => s.mobileNavOpen)
  const setOpen = useUiStore((s) => s.setMobileNavOpen)
  const reduceMotion = useReducedMotion()
  const panelRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, setOpen])

  const panelMotion = reduceMotion
    ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } }
    : { initial: { x: '-100%' }, animate: { x: 0 }, exit: { x: '-100%' } }

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <motion.button
            type="button"
            aria-label="Close menu"
            className="overlay-scrim absolute inset-0 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
          />
          <motion.aside
            ref={panelRef}
            className="surface-workspace-drawer absolute left-0 top-0 flex h-full w-[280px] flex-col border-r bg-[var(--ws-surface-raised,#fff)] shadow-lg"
            initial={panelMotion.initial}
            animate={panelMotion.animate}
            exit={panelMotion.exit}
            transition={{ duration: reduceMotion ? 0.15 : 0.25 }}
          >
            <div className="flex h-[52px] items-center justify-between border-b border-[var(--ws-border)] px-4">
              <span className="text-sm font-semibold text-[var(--ws-text-primary)]">Menu</span>
              <IconButton label="Close menu" onClick={() => setOpen(false)}>
                <X className="h-4 w-4" aria-hidden />
              </IconButton>
            </div>
            <nav aria-label="Main navigation" className="ws-sidebar flex flex-1 flex-col overflow-hidden">
              <div className="ws-sidebar-scroll flex-1">
                <SidebarNavSections
                  sections={navSections}
                  collapsed={false}
                  iconSize="h-5 w-5"
                  onNavigate={() => setOpen(false)}
                />
              </div>
              <SidebarSettingsFooter
                collapsed={false}
                iconSize="h-5 w-5"
                onNavigate={() => setOpen(false)}
                className="ws-sidebar-footer"
              />
            </nav>
          </motion.aside>
        </div>
      )}
    </AnimatePresence>
  )
}
