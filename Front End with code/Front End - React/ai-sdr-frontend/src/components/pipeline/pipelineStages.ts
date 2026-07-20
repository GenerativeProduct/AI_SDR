import type { LucideIcon } from 'lucide-react'
import {
  Brain,
  Compass,
  FlaskConical,
  Mail,
  Repeat,
  Search,
  Target,
} from 'lucide-react'

export type PipelineStageId =
  | 'icp'
  | 'discovery'
  | 'enrichment'
  | 'intelligence'
  | 'qualification'
  | 'outreach'
  | 'follow-up'

export type PipelineStage = {
  id: PipelineStageId
  label: string
  shortLabel: string
  icon: LucideIcon
}

export const PIPELINE_STAGES: PipelineStage[] = [
  { id: 'icp', label: 'ICP setup', shortLabel: 'ICP', icon: Target },
  { id: 'discovery', label: 'Prospect discovery', shortLabel: 'Discovery', icon: Compass },
  { id: 'enrichment', label: 'Account enrichment', shortLabel: 'Enrich', icon: Search },
  { id: 'intelligence', label: 'Prospect intelligence', shortLabel: 'Intel', icon: Brain },
  { id: 'qualification', label: 'Qualification', shortLabel: 'Qualify', icon: FlaskConical },
  { id: 'outreach', label: 'Outreach drafting', shortLabel: 'Outreach', icon: Mail },
  { id: 'follow-up', label: 'Follow-up planning', shortLabel: 'Follow-up', icon: Repeat },
]

export const PIPELINE_EXAMPLE_PROMPTS = [
  'Mid-market SaaS in the US with RevOps leaders struggling with pipeline visibility and forecast accuracy.',
  'Series B fintech companies hiring VP Sales and investing in outbound automation this quarter.',
  'Healthcare tech providers with 200–800 employees expanding into enterprise accounts in North America.',
] as const

export function stageIndexFromProgress(progress: number) {
  return Math.min(
    PIPELINE_STAGES.length - 1,
    Math.floor((progress / 100) * PIPELINE_STAGES.length),
  )
}
