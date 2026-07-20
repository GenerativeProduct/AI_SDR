import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../client'
import { unwrapListItems } from '../listUtils'
import { queryKeys } from '../queryKeys'
import type {
  ConversationThread,
  CRMSyncRecord,
  DashboardResponse,
  DiscoveredAccount,
  DiscoveredContact,
  EnrichmentResult,
  FollowUpPlan,
  JobCreateResponse,
  JobStatusResponse,
  ListResponse,
  MeetingBooking,
  OutreachCampaign,
  ProspectIntelligenceResult,
  QualificationResult,
  SDRPipelineResponse,
} from '../types'

export function useDashboard() {
  return useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: () => api.get<DashboardResponse>('/sdr/dashboard'),
  })
}

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => api.get<{ status: string }>('/health'),
    refetchInterval: 30_000,
  })
}

export function useJobPoll(jobId: string | null) {
  return useQuery({
    queryKey: queryKeys.pipeline.job(jobId),
    queryFn: () => api.get<JobStatusResponse>(`/sdr/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (q) => {
      const status = q.state.data?.status
      return status === 'completed' || status === 'failed' ? false : 1500
    },
  })
}

export function useIcpList() {
  return useQuery({
    queryKey: queryKeys.icp.list(),
    queryFn: () =>
      api.get<{ items: { icp_id: string; icp_name: string; version: number }[]; total: number }>(
        '/icp',
      ),
  })
}

export function useIcpDetail(icpId: string | null, version?: number) {
  return useQuery({
    queryKey: queryKeys.icp.detail(icpId ?? '', version),
    queryFn: () => {
      const qs = version != null ? `?version=${version}` : ''
      return api.get<Record<string, unknown>>(`/icp/${icpId}${qs}`)
    },
    enabled: Boolean(icpId),
  })
}

export function useIcpVersions(icpId: string | null) {
  return useQuery({
    queryKey: queryKeys.icp.versions(icpId ?? ''),
    queryFn: () =>
      api.get<{ version_id: string; version: number; status: string; icp_name: string }[]>(
        `/icp/${icpId}/versions`,
      ),
    enabled: Boolean(icpId),
  })
}

export function useDiscoveryStatus() {
  return useQuery({
    queryKey: queryKeys.discovery.status(),
    queryFn: () => api.get<Record<string, unknown>>('/prospect-discovery/status'),
  })
}

export function useDiscoveredAccounts(icpId?: string) {
  return useQuery({
    queryKey: queryKeys.discovery.accounts(icpId),
    queryFn: () => {
      const qs = icpId ? `?icp_id=${icpId}` : ''
      return api.get<DiscoveredAccount[]>(`/prospect-discovery/accounts${qs}`)
    },
  })
}

export function useDiscoveredContacts(accountId?: string) {
  return useQuery({
    queryKey: queryKeys.discovery.contacts(accountId),
    queryFn: () => {
      const qs = accountId ? `?account_id=${accountId}` : ''
      return api.get<DiscoveredContact[]>(`/prospect-discovery/contacts${qs}`)
    },
  })
}

export function useEnrichmentList() {
  return useQuery({
    queryKey: queryKeys.enrichment.list(),
    queryFn: async () => {
      const res = await api.get<ListResponse<EnrichmentResult>>('/enrichment')
      return unwrapListItems(res)
    },
  })
}

export function useEnrichmentStatus() {
  return useQuery({
    queryKey: queryKeys.enrichment.status(),
    queryFn: () => api.get<Record<string, unknown>>('/enrichment/status'),
  })
}

export function useIntelligenceList(accountId?: string) {
  return useQuery({
    queryKey: queryKeys.intelligence.list(accountId),
    queryFn: async () => {
      const qs = accountId ? `?account_id=${accountId}` : ''
      const res = await api.get<ListResponse<ProspectIntelligenceResult>>(`/prospect-intelligence${qs}`)
      return unwrapListItems(res)
    },
  })
}

export function useIntelligenceRankingStatus() {
  return useQuery({
    queryKey: queryKeys.intelligence.rankingStatus(),
    queryFn: () => api.get<Record<string, unknown>>('/prospect-intelligence/ranking/status'),
  })
}

export function useQualificationList(accountId?: string) {
  return useQuery({
    queryKey: queryKeys.qualification.list(accountId),
    queryFn: async () => {
      const qs = accountId ? `?account_id=${accountId}` : ''
      const res = await api.get<ListResponse<QualificationResult>>(`/qualification${qs}`)
      return unwrapListItems(res)
    },
  })
}

export function useCampaigns(status?: string) {
  return useQuery({
    queryKey: queryKeys.outreach.campaigns(status),
    queryFn: () =>
      api.get<ListResponse<OutreachCampaign>>(
        `/outreach/campaigns${status ? `?status=${status}` : ''}`,
      ),
  })
}

export function useOutreachPerformance() {
  return useQuery({
    queryKey: queryKeys.outreach.performance,
    queryFn: () => api.get<Record<string, unknown>>('/outreach/performance'),
  })
}

export function useConversations(status?: string) {
  return useQuery({
    queryKey: queryKeys.conversations.list(status),
    queryFn: () =>
      api.get<ListResponse<ConversationThread>>(
        `/conversations${status ? `?status=${status}` : ''}`,
      ),
  })
}

export function useConversationDetail(id: string | null) {
  return useQuery({
    queryKey: queryKeys.conversations.detail(id ?? ''),
    queryFn: () => api.get<ConversationThread>(`/conversations/${id}`),
    enabled: Boolean(id),
  })
}

export function useConversationAgentStatus() {
  return useQuery({
    queryKey: queryKeys.conversations.agentStatus,
    queryFn: () => api.get<Record<string, unknown>>('/conversations/agent/status'),
  })
}

export function useFollowUpPlans(status?: string) {
  return useQuery({
    queryKey: queryKeys.followUp.plans(status),
    queryFn: () =>
      api.get<ListResponse<FollowUpPlan>>(
        `/follow-up/plans${status ? `?status=${status}` : ''}`,
      ),
  })
}

export function useFollowUpSchedulerStatus() {
  return useQuery({
    queryKey: queryKeys.followUp.schedulerStatus,
    queryFn: () => api.get<Record<string, unknown>>('/follow-up/scheduler/status'),
  })
}

export function useMeetings(status?: string) {
  return useQuery({
    queryKey: queryKeys.meetings.list(status),
    queryFn: () =>
      api.get<ListResponse<MeetingBooking>>(`/meetings${status ? `?status=${status}` : ''}`),
  })
}

export function useMeetingsStatus() {
  return useQuery({
    queryKey: queryKeys.meetings.status,
    queryFn: () => api.get<Record<string, unknown>>('/meetings/status'),
  })
}

export function useCrmSyncs() {
  return useQuery({
    queryKey: queryKeys.crm.syncs,
    queryFn: () => api.get<CRMSyncRecord[]>('/crm/syncs'),
  })
}

export function useCrmStatus() {
  return useQuery({
    queryKey: queryKeys.crm.status,
    queryFn: () => api.get<Record<string, unknown>>('/crm/status'),
  })
}

export function useRunPipeline() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api.post<JobCreateResponse>('/sdr/pipeline/run', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.dashboard }),
  })
}

export function useRunDiscovery() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api.post<Record<string, unknown>>('/prospect-discovery/run', body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.discovery.all })
      qc.invalidateQueries({ queryKey: queryKeys.dashboard })
    },
  })
}

export function invalidateDashboard(qc: ReturnType<typeof useQueryClient>) {
  return qc.invalidateQueries({ queryKey: queryKeys.dashboard })
}

export type { SDRPipelineResponse, JobStatusResponse }
