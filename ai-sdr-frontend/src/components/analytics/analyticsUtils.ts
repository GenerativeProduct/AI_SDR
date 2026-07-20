import type {
  MeetingBooking,
  OutreachCampaign,
  ProspectIntelligenceResult,
  QualificationResult,
} from '../../api/types'

export type AnalyticsRow = {
  stage: string
  contact_id?: string
  campaign_id?: string
  meeting_id?: string
  contact_name?: string
  status?: string
}

export function buildAnalyticsRows(input: {
  intelligence: ProspectIntelligenceResult[]
  qualification: QualificationResult[]
  campaigns: OutreachCampaign[]
  meetings: MeetingBooking[]
}): AnalyticsRow[] {
  return [
    ...input.intelligence.map((r) => ({
      stage: 'intelligence',
      contact_name: r.contact_name,
      status: r.ranking?.priority_band,
      contact_id: r.contact_id,
    })),
    ...input.qualification.map((r) => ({
      stage: 'qualification',
      contact_name: r.contact_name,
      status: r.qualification_status,
      contact_id: r.contact_id,
    })),
    ...input.campaigns.map((r) => ({
      stage: 'outreach',
      contact_name: r.contact_name,
      status: r.status,
      campaign_id: r.campaign_id,
    })),
    ...input.meetings.map((r) => ({
      stage: 'meeting',
      contact_name: r.contact_name,
      status: r.status,
      meeting_id: r.meeting_id,
    })),
  ]
}

export function exportAnalyticsCsv(rows: AnalyticsRow[]) {
  const header = 'stage,id,status,contact\n'
  const body = rows
    .map((r) =>
      [r.stage, r.contact_id ?? r.campaign_id ?? r.meeting_id, r.status, r.contact_name]
        .map((v) => `"${String(v ?? '')}"`)
        .join(','),
    )
    .join('\n')
  const blob = new Blob([header + body], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'sdr-analytics.csv'
  a.click()
  URL.revokeObjectURL(url)
}
