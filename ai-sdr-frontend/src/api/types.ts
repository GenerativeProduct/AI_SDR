export type UserRole = 'operator' | 'manager' | 'admin'

export interface UserPublic {
  user_id: string
  email: string
  display_name: string
  role: UserRole
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface DashboardResponse {
  icp_count: number
  accounts_count: number
  contacts_count: number
  enrichments_count: number
  intelligence_count: number
  qualified_sql_mql: number
  pending_campaigns: number
  active_conversations: number
  upcoming_meetings: number
  crm_sync_failures: number
  follow_up_plans_pending: number
}

export interface JobCreateResponse {
  job_id: string
  status: string
}

export interface JobStatusResponse {
  job_id: string
  job_type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  result?: SDRPipelineResponse
  error?: string
}

export interface SDRPipelineResponse {
  icp_definition: Record<string, unknown>
  discovered_accounts: DiscoveredAccount[]
  discovered_contacts: DiscoveredContact[]
  enriched_results: EnrichmentResult[]
  prospect_intelligence: ProspectIntelligenceResult[]
  qualification_results: QualificationResult[]
  outreach_campaigns: OutreachCampaign[]
  follow_up_plans: FollowUpPlan[]
  warnings: string[]
  summary: Record<string, number>
}

export interface ICPSuggestionResponse {
  personas: string[]
  pain_points: string[]
  exclusions: Record<string, unknown>
  reasoning: string
  source: string
}

export interface ICPValidationResult {
  status: string
  warnings: string[]
  normalized_definition: Record<string, unknown>
}

export interface OutreachCampaign {
  campaign_id: string
  status: string
  contact_name?: string
  channel?: string
  subject?: string
  body?: string
  [key: string]: unknown
}

export interface ConversationThread {
  conversation_id: string
  status: string
  classification?: string
  inbound_message?: string
  draft_reply?: string
  [key: string]: unknown
}

export interface MeetingBooking {
  meeting_id: string
  status: string
  contact_name?: string
  scheduled_at?: string
  [key: string]: unknown
}

export interface ListResponse<T> {
  items: T[]
  total: number
}

export interface DiscoveredAccount {
  account_id: string
  icp_id: string
  company_name: string
  website?: string | null
  linkedin_url?: string | null
  industry: string
  location: string
  employee_count: number
  revenue_range?: string | null
  source: string
  fit_score: number
  fit_reasons?: string[]
  status: string
  discovered_at?: string
}

export interface DiscoveredContact {
  contact_id: string
  account_id: string
  full_name: string
  title: string
  department: string
  seniority: string
  email?: string | null
  linkedin_url?: string | null
  phone?: string | null
  email_verification_status: string
  phone_verification_status: string
  source: string
  persona_match_score: number
  confidence: number
  status: string
  discovered_at?: string
}
export interface EnrichmentSignal {
  type: string
  detail: string
  confidence: number
  source_url?: string | null
}

export interface EnrichmentResult {
  enrichment_id?: string
  account_id: string
  company_name: string
  status: string
  collection: string
  company_summary: string
  products_services?: string[]
  target_customers?: string[]
  signals?: EnrichmentSignal[]
  pain_point_hypotheses?: string[]
  personalization_angles?: string[]
  contact_briefs?: Record<string, unknown>[]
  recommended_next_action: string
  confidence_score: number
  created_at?: string
}

export interface ProbabilityEstimate {
  value: number
  mode: 'heuristic' | 'model'
  calibrated: boolean
  model_name: string
  model_version: string
  reasons?: string[]
}

export interface IntentAssessment {
  probability: ProbabilityEstimate
  level: 'high' | 'medium' | 'low'
  recommended_timing: string
}

export interface PropensityAssessment {
  reply_probability: ProbabilityEstimate
  meeting_probability: ProbabilityEstimate
  qualification_probability: ProbabilityEstimate
}

export interface RankingResult {
  priority_score: number
  rank?: number | null
  priority_band: 'high' | 'medium' | 'low'
  provider: string
  reasons?: string[]
}

export interface ProspectIntelligenceResult {
  intelligence_id?: string
  account_id: string
  contact_id: string
  company_name: string
  contact_name: string
  intent: IntentAssessment
  propensity: PropensityAssessment
  ranking: RankingResult
  created_at?: string
}

export interface FrameworkCriterion {
  name: string
  score: number
  confidence: number
  evidence?: string[]
  missing_information?: string[]
}

export interface BANTAssessment {
  framework: 'BANT'
  score: number
  budget: FrameworkCriterion
  authority: FrameworkCriterion
  need: FrameworkCriterion
  timeline: FrameworkCriterion
}

export interface MEDDICAssessment {
  framework: 'MEDDIC'
  score: number
  metrics: FrameworkCriterion
  economic_buyer: FrameworkCriterion
  decision_criteria: FrameworkCriterion
  decision_process: FrameworkCriterion
  identified_pain: FrameworkCriterion
  champion: FrameworkCriterion
}

export interface QualificationResult {
  qualification_id?: string
  intelligence_id: string
  account_id: string
  contact_id: string
  company_name: string
  contact_name: string
  bant?: BANTAssessment | null
  meddic?: MEDDICAssessment | null
  ml_qualification_probability: number
  qualification_score: number
  qualification_tier: 'Tier 1' | 'Tier 2' | 'Tier 3'
  qualification_status: 'SQL' | 'MQL' | 'Nurture' | 'Disqualified'
  sales_ready: boolean
  next_action: string
  reasoning?: string[]
  missing_information?: string[]
}

export interface FollowUpTouch {
  touch_id?: string
  sequence_order: number
  delay_hours: number
  channel: 'email' | 'linkedin' | 'phone' | 'sms' | 'whatsapp'
  subject?: string | null
  body: string
  scheduled_at: string
  status: 'pending_approval' | 'approved' | 'queued' | 'sent' | 'human_task' | 'failed' | 'suppressed'
}

export interface FollowUpPlan {
  plan_id?: string
  campaign_id: string
  contact_id: string
  status: 'pending_approval' | 'active' | 'paused' | 'stopped' | 'completed'
  touches?: FollowUpTouch[]
  approved_by?: string | null
  stop_reason?: string | null
  scheduler_backend: 'local' | 'temporal'
}

export interface CRMSyncRecord {
  sync_id?: string
  meeting_id: string
  provider: string
  status: 'pending' | 'synced' | 'failed'
  company_id?: string | null
  person_id?: string | null
  opportunity_id?: string | null
  provider_payload?: Record<string, unknown>
  error?: string | null
  created_at?: string
}
