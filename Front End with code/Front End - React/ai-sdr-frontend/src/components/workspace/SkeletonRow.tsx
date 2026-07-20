export function SkeletonRow() {
  return (
    <div className="ws-row flex items-center gap-3 px-4 py-3" aria-hidden>
      <div className="ws-skeleton h-9 w-9 shrink-0 rounded-full" />
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <div className="ws-skeleton h-3 w-3/5 max-w-[200px]" />
        <div className="ws-skeleton h-2.5 w-4/5 max-w-[280px]" />
      </div>
      <div className="ws-skeleton h-5 w-16 shrink-0 rounded-full" />
    </div>
  )
}

export function SkeletonPanel({ lines = 4 }: { lines?: number }) {
  return (
    <div className="space-y-3 p-4" aria-busy="true" aria-label="Loading">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="ws-skeleton h-3 w-full" style={{ width: `${90 - i * 10}%` }} />
      ))}
    </div>
  )
}
