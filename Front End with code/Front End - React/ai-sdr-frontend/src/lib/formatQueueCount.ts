/** Compact count for queue chips and labels (e.g. 1.2k, 12k+). */
export function formatQueueCount(count: number): string {
  if (count < 0 || !Number.isFinite(count)) return '0'
  if (count < 1000) return String(count)
  if (count < 10000) {
    const k = count / 1000
    return k % 1 === 0 ? `${k}k` : `${k.toFixed(1)}k`
  }
  if (count < 1_000_000) return `${Math.floor(count / 1000)}k+`
  return `${(count / 1_000_000).toFixed(1)}m+`
}
