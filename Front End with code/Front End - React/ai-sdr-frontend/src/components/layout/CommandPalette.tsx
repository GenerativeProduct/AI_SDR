import { AnimatePresence, motion } from 'framer-motion'
import { Search } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { navSections, settingsNav } from '../../config/navigation'
import { Input } from '../ui/Input'
import { useUiStore } from '../../stores/uiStore'

export function CommandPalette() {
  const open = useUiStore((s) => s.commandPaletteOpen)
  const setOpen = useUiStore((s) => s.setCommandPaletteOpen)
  const [query, setQuery] = useState('')
  const [highlight, setHighlight] = useState(0)
  const navigate = useNavigate()
  const dialogRef = useRef<HTMLDivElement>(null)

  const close = useCallback(() => {
    setOpen(false)
    setQuery('')
  }, [setOpen])

  useEffect(() => {
    if (!open) return
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  const navItems = useMemo(
    () =>
      navSections.flatMap((s) =>
        s.items.map((i) => ({ ...i, section: s.title })),
      ),
    [],
  )

  const allItems = useMemo(() => {
    const settings = { ...settingsNav, section: 'System' }
    const q = query.trim().toLowerCase()
    const items = [...navItems, settings]
    if (!q) return items
    return items.filter(
      (i) => i.label.toLowerCase().includes(q) || i.section.toLowerCase().includes(q),
    )
  }, [navItems, query])

  useEffect(() => setHighlight(0), [query])

  const go = useCallback(
    (path: string) => {
      navigate(path)
      close()
    },
    [navigate, close],
  )

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setHighlight((h) => Math.min(h + 1, allItems.length - 1))
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setHighlight((h) => Math.max(h - 1, 0))
      }
      if (e.key === 'Enter' && allItems[highlight]) {
        e.preventDefault()
        go(allItems[highlight].path)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, allItems, highlight, go])

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[60] flex items-start justify-center px-4 pt-[10vh] md:pt-[15vh]">
          <motion.button
            type="button"
            aria-label="Close command palette"
            className="overlay-scrim absolute inset-0 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={close}
          />
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
            className="surface-workspace-command relative flex max-h-[80vh] w-full max-w-xl flex-col overflow-hidden rounded-2xl border border-[var(--ws-border)] bg-[var(--ws-surface-raised,#fff)] shadow-[0_18px_48px_rgba(0,0,0,0.12)]"
            initial={{ opacity: 0, scale: 0.98, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -8 }}
            transition={{ duration: 0.15 }}
          >
            <div className="border-b border-[var(--ws-border)] p-3">
              <Input
                autoFocus
                placeholder="Search modules…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                leftIcon={<Search className="h-4 w-4" />}
              />
            </div>
            <ul className="flex-1 overflow-y-auto p-2">
              <p className="px-2 py-1 text-2xs font-medium uppercase tracking-wide text-[var(--ws-text-caption)]">
                Navigation
              </p>
              {allItems.map((item, i) => (
                <li key={item.path}>
                  <button
                    type="button"
                    className={
                      highlight === i
                        ? 'flex w-full items-center gap-3 rounded-lg bg-zinc-100 px-3 py-2.5 text-left text-sm'
                        : 'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm hover:bg-zinc-50'
                    }
                    onClick={() => go(item.path)}
                  >
                    <item.icon className="h-4 w-4 text-[var(--ws-text-caption)]" />
                    <span className="flex-1 text-[var(--ws-text-primary)]">{item.label}</span>
                    <span className="text-2xs text-[var(--ws-text-caption)]">{item.section}</span>
                  </button>
                </li>
              ))}
              {allItems.length === 0 && (
                <li className="px-3 py-6 text-center text-sm text-[var(--ws-text-caption)]">No results</li>
              )}
            </ul>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
