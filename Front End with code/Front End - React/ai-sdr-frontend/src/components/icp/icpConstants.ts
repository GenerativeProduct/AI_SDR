export type IcpWeights = {
  industry_fit: number
  company_size_fit: number
  persona_fit: number
  geo_fit: number
  pain_point_fit: number
}

export const DEFAULT_ICP_WEIGHTS: IcpWeights = {
  industry_fit: 0.3,
  company_size_fit: 0.2,
  persona_fit: 0.25,
  geo_fit: 0.1,
  pain_point_fit: 0.15,
}

export type IcpWeightKey = keyof IcpWeights

export const ICP_WEIGHT_META: Record<IcpWeightKey, { label: string; hint: string }> = {
  industry_fit: { label: 'Industry fit', hint: 'Vertical and sector alignment' },
  company_size_fit: { label: 'Company size', hint: 'Employee and revenue band match' },
  persona_fit: { label: 'Persona fit', hint: 'Title and buying-role relevance' },
  geo_fit: { label: 'Geography', hint: 'Region and market coverage' },
  pain_point_fit: { label: 'Pain points', hint: 'Problem-solution resonance' },
}

export const ICP_CRITERIA_PRESETS = [
  {
    label: 'Mid-market SaaS',
    industries: 'SaaS, B2B Software',
    geographies: 'US, Canada',
    personas: 'RevOps, VP Sales',
    painPoints: 'Pipeline visibility, forecast accuracy',
  },
  {
    label: 'Enterprise fintech',
    industries: 'Fintech, Financial Services',
    geographies: 'US, UK',
    personas: 'CRO, Head of Growth',
    painPoints: 'Outbound efficiency, compliance-aware outreach',
  },
] as const
