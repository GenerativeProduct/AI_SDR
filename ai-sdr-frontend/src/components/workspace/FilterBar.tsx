import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '../../lib/cn'
import { formatQueueCount } from '../../lib/formatQueueCount'

export type FilterOption = {
  id: string
  label: string
  count?: number
}

type FilterBarProps = {
  options: FilterOption[]
  activeId: string
  onChange: (id: string) => void
  'aria-label'?: string
}

export function FilterBar({
  options,
  activeId,
  onChange,
  'aria-label': ariaLabel = 'Filters',
}: FilterBarProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  const updateScrollState = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    const { scrollLeft, scrollWidth, clientWidth } = el
    setCanScrollLeft(scrollLeft > 4)
    setCanScrollRight(scrollLeft + clientWidth < scrollWidth - 4)
  }, [])

  const scrollBy = (direction: 'left' | 'right') => {
    const el = scrollRef.current
    if (!el) return
    const delta = Math.max(200, el.clientWidth * 0.6)
    el.scrollBy({ left: direction === 'left' ? -delta : delta, behavior: 'smooth' })
  }

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    updateScrollState()
    el.addEventListener('scroll', updateScrollState, { passive: true })
    const ro = new ResizeObserver(updateScrollState)
    ro.observe(el)
    return () => {
      el.removeEventListener('scroll', updateScrollState)
      ro.disconnect()
    }
  }, [options.length, updateScrollState])

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const active = el.querySelector<HTMLElement>(`[data-filter-id="${activeId}"]`)
    active?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
    updateScrollState()
  }, [activeId, options.length, updateScrollState])

  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        aria-label="Scroll filters left"
        disabled={!canScrollLeft}
        onClick={() => scrollBy('left')}
        className={cn(
          'ws-focus-ring flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[var(--ws-border)] bg-[var(--ws-surface-raised,#fff)] text-[var(--ws-text-secondary)] transition-colors',
          !canScrollLeft && 'cursor-not-allowed opacity-50',
          canScrollLeft && 'hover:bg-[var(--ws-canvas)]',
        )}
      >
        <ChevronLeft className="h-4 w-4" aria-hidden />
      </button>

      <div
        ref={scrollRef}
        className="flex min-w-0 flex-1 gap-2 overflow-x-auto overflow-y-visible py-1 scrollbar-none"
        role="tablist"
        aria-label={ariaLabel}
      >
        {options.map((opt) => {
          const isActive = activeId === opt.id
          const countLabel = opt.count != null ? formatQueueCount(opt.count) : null

          return (
            <button
              key={opt.id}
              type="button"
              role="tab"
              data-filter-id={opt.id}
              aria-selected={isActive}
              onClick={() => onChange(opt.id)}
              title={
                opt.count != null && opt.count >= 1000
                  ? `${opt.label}: ${opt.count.toLocaleString()}`
                  : undefined
              }
              className={cn(
                'ws-focus-ring shrink-0 rounded-full border px-4 py-2 text-sm font-medium transition-[background-color,border-color,color] duration-150',
                isActive ? 'ws-filter-pill--active' : 'ws-filter-pill',
              )}
            >
              {opt.label}
              {countLabel != null ? (
                <span className="ml-1.5 tabular-nums opacity-75">({countLabel})</span>
              ) : null}
            </button>
          )
        })}
      </div>

      <button
        type="button"
        aria-label="Scroll filters right"
        disabled={!canScrollRight}
        onClick={() => scrollBy('right')}
        className={cn(
          'ws-focus-ring flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[var(--ws-border)] bg-[var(--ws-surface-raised,#fff)] text-[var(--ws-text-secondary)] transition-colors',
          !canScrollRight && 'cursor-not-allowed opacity-50',
          canScrollRight && 'hover:bg-[var(--ws-canvas)]',
        )}
      >
        <ChevronRight className="h-4 w-4" aria-hidden />
      </button>
    </div>
  )
}
