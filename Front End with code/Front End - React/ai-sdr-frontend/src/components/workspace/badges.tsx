import type { ReactNode } from 'react'
import { Mail, MessageSquare, Phone } from 'lucide-react'
import { cn } from '../../lib/cn'

const statusStyles: Record<string, string> = {
  draft: 'bg-zinc-100 text-zinc-600 ring-zinc-200/60',
  pending_approval: 'bg-amber-50 text-amber-800 ring-amber-200/60',
  approved: 'bg-sky-50 text-sky-700 ring-sky-200/70',
  running: 'bg-blue-50 text-blue-800 ring-blue-200/70',
  paused: 'bg-orange-50 text-orange-700 ring-orange-200/60',
  completed: 'bg-emerald-50 text-emerald-700 ring-emerald-200/60',
  cancelled: 'bg-red-50 text-red-700 ring-red-200/60',
  booked: 'bg-emerald-50 text-emerald-700 ring-emerald-200/60',
  failed: 'bg-red-50 text-red-700 ring-red-200/60',
  synced: 'bg-emerald-50 text-emerald-700 ring-emerald-200/60',
  SQL: 'bg-emerald-50 text-emerald-700 ring-emerald-200/60',
  MQL: 'bg-sky-50 text-sky-700 ring-sky-200/70',
  Nurture: 'bg-amber-50 text-amber-800 ring-amber-200/60',
  Disqualified: 'bg-red-50 text-red-700 ring-red-200/60',
}

function formatLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function StatusBadge({ status }: { status: string }) {
  const key = status.toLowerCase()
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset capitalize',
        statusStyles[key] ?? statusStyles[status] ?? 'bg-zinc-100 text-zinc-600 ring-zinc-200/60',
      )}
    >
      {formatLabel(status)}
    </span>
  )
}

export function QualificationBadge({ tier }: { tier: string }) {
  return <StatusBadge status={tier} />
}

const channelIcons: Record<string, typeof Mail> = {
  email: Mail,
  linkedin: MessageSquare,
  phone: Phone,
  sms: MessageSquare,
  whatsapp: MessageSquare,
}

export function CampaignChannelBadge({ channel }: { channel: string }) {
  const Icon = channelIcons[channel] ?? Mail
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-[var(--ws-text-secondary)] ring-1 ring-inset ring-zinc-200/80">
      <Icon className="h-3 w-3" aria-hidden />
      <span className="capitalize">{channel.replace('_', ' ')}</span>
    </span>
  )
}

export function MetricChip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-lg bg-white/80 px-2 py-1 text-xs font-medium text-zinc-600 ring-1 ring-zinc-200/80">
      {children}
    </span>
  )
}
