export const FOLLOW_UP_FILTERS = [
  { id: '', label: 'All' },
  { id: 'pending_approval', label: 'Pending' },
  { id: 'active', label: 'Active' },
  { id: 'paused', label: 'Paused' },
  { id: 'completed', label: 'Completed' },
] as const

export function planKey(plan: { plan_id?: string; campaign_id: string; contact_id: string }) {
  return plan.plan_id ?? `${plan.campaign_id}-${plan.contact_id}`
}
