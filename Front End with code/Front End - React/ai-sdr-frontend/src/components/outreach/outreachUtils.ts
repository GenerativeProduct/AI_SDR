import type { OutreachCampaign } from '../../api/types'

export function formatCount(value: number) {
  return value.toLocaleString()
}

export function campaignKey(campaign: OutreachCampaign) {
  return campaign.campaign_id
}

export const OUTREACH_FILTERS = [
  { id: 'pending_approval', label: 'Pending' },
  { id: 'approved', label: 'Approved' },
  { id: 'running', label: 'Running' },
  { id: 'paused', label: 'Paused' },
  { id: 'completed', label: 'Completed' },
  { id: 'cancelled', label: 'Cancelled' },
] as const

export function performanceMetrics(perf: Record<string, unknown> | undefined) {
  if (!perf) return []
  return [
    { label: 'Sent', value: Number(perf.sent ?? perf.total_sent ?? 0) },
    { label: 'Opened', value: Number(perf.opened ?? perf.total_opened ?? 0) },
    { label: 'Replied', value: Number(perf.replied ?? perf.total_replied ?? 0) },
    { label: 'Meetings', value: Number(perf.meetings ?? perf.total_meetings ?? 0) },
  ]
}
