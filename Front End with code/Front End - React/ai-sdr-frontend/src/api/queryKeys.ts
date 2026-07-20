export const queryKeys = {
  health: ['health'] as const,
  dashboard: ['dashboard'] as const,
  icp: {
    all: ['icp'] as const,
    list: () => [...queryKeys.icp.all, 'list'] as const,
    detail: (id: string, version?: number) =>
      [...queryKeys.icp.all, id, version ?? 'latest'] as const,
    versions: (id: string) => [...queryKeys.icp.all, id, 'versions'] as const,
  },
  discovery: {
    all: ['discovery'] as const,
    status: () => [...queryKeys.discovery.all, 'status'] as const,
    accounts: (icpId?: string) => [...queryKeys.discovery.all, 'accounts', icpId ?? 'all'] as const,
    contacts: (accountId?: string) =>
      [...queryKeys.discovery.all, 'contacts', accountId ?? 'all'] as const,
  },
  enrichment: {
    all: ['enrichment'] as const,
    list: () => [...queryKeys.enrichment.all, 'list'] as const,
    status: () => [...queryKeys.enrichment.all, 'status'] as const,
    detail: (accountId: string) => [...queryKeys.enrichment.all, accountId] as const,
  },
  intelligence: {
    all: ['intelligence'] as const,
    list: (accountId?: string) => [...queryKeys.intelligence.all, 'list', accountId ?? 'all'] as const,
    rankingStatus: () => [...queryKeys.intelligence.all, 'ranking-status'] as const,
  },
  qualification: {
    all: ['qualification'] as const,
    list: (accountId?: string) =>
      [...queryKeys.qualification.all, 'list', accountId ?? 'all'] as const,
  },
  pipeline: {
    job: (jobId: string | null) => ['pipeline-job', jobId] as const,
  },
  outreach: {
    campaigns: (status?: string) => ['campaigns', status ?? 'all'] as const,
    performance: ['outreach-performance'] as const,
    detail: (id: string) => ['campaign', id] as const,
  },
  conversations: {
    list: (status?: string) => ['conversations', status ?? 'all'] as const,
    detail: (id: string) => ['conversation', id] as const,
    agentStatus: ['conversation-agent-status'] as const,
  },
  followUp: {
    plans: (status?: string) => ['follow-up-plans', status ?? 'all'] as const,
    schedulerStatus: ['follow-up-scheduler-status'] as const,
  },
  meetings: {
    list: (status?: string) => ['meetings', status ?? 'all'] as const,
    status: ['meetings-status'] as const,
  },
  crm: {
    syncs: ['crm-syncs'] as const,
    status: ['crm-status'] as const,
  },
  auth: {
    me: ['auth-me'] as const,
  },
}
