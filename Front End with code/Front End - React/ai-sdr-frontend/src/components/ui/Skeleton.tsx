import { cn } from '../../lib/utils'

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn('rounded-md skeleton-shimmer bg-subtle', className)} aria-hidden />
  )
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-xl border border-border-subtle bg-surface p-4">
      <Skeleton className="mb-3 h-3 w-20" />
      <Skeleton className="mb-2 h-8 w-24" />
      <Skeleton className="h-10 w-full" />
    </div>
  )
}

export function ListSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-busy aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full rounded-lg" />
      ))}
    </div>
  )
}
