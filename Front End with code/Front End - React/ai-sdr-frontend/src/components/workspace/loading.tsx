import { SkeletonPanel, SkeletonRow } from './SkeletonRow'

export function ListLoading({ rows = 5 }: { rows?: number }) {
  return (
    <div className="overflow-hidden rounded-xl border border-[var(--ws-border)] bg-[var(--ws-surface-raised,#fff)]">
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonRow key={i} />
      ))}
    </div>
  )
}

export function KpiGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className={`ws-kpi-grid ${count >= 6 ? 'ws-kpi-grid--6' : ''}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="ws-kpi-tile">
          <div className="ws-skeleton h-3 w-16 rounded" />
          <div className="ws-skeleton mt-3 h-8 w-20 rounded" />
        </div>
      ))}
    </div>
  )
}

export function CardGridSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="ws-card">
          <SkeletonPanel lines={3} />
        </div>
      ))}
    </div>
  )
}

export function FunnelSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="ws-funnel-skeleton" aria-busy aria-label="Loading funnel">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i}>
          <div className="mb-1 flex justify-between">
            <div className="ws-skeleton h-4 w-32 rounded" />
            <div className="ws-skeleton h-4 w-8 rounded" />
          </div>
          <div className="ws-funnel-track">
            <div className="ws-skeleton h-full rounded-full" style={{ width: `${90 - i * 8}%` }} />
          </div>
        </div>
      ))}
    </div>
  )
}

export function TableSkeleton({ rows = 6, cols = 3 }: { rows?: number; cols?: number }) {
  return (
    <div className="overflow-hidden rounded-xl border border-[var(--ws-border)]">
      <div className="flex gap-4 border-b border-[var(--ws-border)] px-3 py-2">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="ws-skeleton h-4 flex-1 rounded" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 border-t border-[var(--ws-border)] px-3 py-3">
          {Array.from({ length: cols }).map((_, j) => (
            <div key={j} className="ws-skeleton h-4 flex-1 rounded" />
          ))}
        </div>
      ))}
    </div>
  )
}

export function PageLoading({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16" aria-busy aria-label={label}>
      <div className="ws-skeleton h-10 w-10 rounded-full" />
      <p className="text-sm text-[var(--ws-text-muted)]">{label}…</p>
    </div>
  )
}
