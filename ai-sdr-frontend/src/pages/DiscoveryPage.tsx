import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { RefreshCw, Search, Sparkles, Target } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import {
  useDiscoveredAccounts,
  useDiscoveredContacts,
  useDiscoveryStatus,
  useIcpList,
  useJobPoll,
  useRunDiscovery,
} from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import type { JobCreateResponse } from '../api/types'
import { DiscoveryAccountsPanel } from '../components/discovery/DiscoveryAccountsPanel'
import { DiscoveryRunPanel } from '../components/discovery/DiscoveryRunPanel'
import { PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function DiscoveryPage() {
  const qc = useQueryClient()
  const [icpFilter, setIcpFilter] = useState('')
  const [runIcpId, setRunIcpId] = useState('')
  const [runLimit, setRunLimit] = useState('5')
  const [jobId, setJobId] = useState<string | null>(null)

  const icpList = useIcpList()
  const discoveryStatus = useDiscoveryStatus()
  const accounts = useDiscoveredAccounts(icpFilter || undefined)
  const contacts = useDiscoveredContacts()
  const runDiscovery = useRunDiscovery()
  const jobQuery = useJobPoll(jobId)

  const icpOptions = useMemo(
    () => [
      { value: '', label: 'All ICPs' },
      ...(icpList.data?.items?.map((item) => ({ value: item.icp_id, label: item.icp_name })) ?? []),
    ],
    [icpList.data],
  )

  const runIcpOptions = useMemo(
    () => icpList.data?.items?.map((item) => ({ value: item.icp_id, label: item.icp_name })) ?? [],
    [icpList.data],
  )

  const refreshResults = () => {
    accounts.refetch()
    contacts.refetch()
    qc.invalidateQueries({ queryKey: queryKeys.discovery.all })
  }

  const startRun = useMutation({
    mutationFn: async () => {
      const icp = await api.get<Record<string, unknown>>(`/icp/${runIcpId}`)
      return api.post<JobCreateResponse>('/prospect-discovery/run', {
        icp_definition: icp,
        limit: Number(runLimit) || 5,
      })
    },
    onSuccess: (job) => {
      if ('job_id' in job) setJobId(job.job_id)
      toast.success('Discovery run started')
      refreshResults()
    },
    onError: () => toast.error('Discovery run failed'),
  })

  const handleQuickRun = () => {
    runDiscovery.mutate(
      { icp_definition: {}, limit: 3 },
      {
        onSuccess: () => refreshResults(),
      },
    )
  }

  return (
    <section className="sdr-discovery">
      <PageHeader
        embedded
        flush
        className="sdr-discovery__header !mb-0"
        eyebrow="Pipeline"
        title={pageTitles['/discovery'] ?? 'Discovery'}
        description="Find accounts and contacts that match your ICP — review fit, expand contacts, and queue enrichment."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={accounts.isFetching || contacts.isFetching}
              onClick={refreshResults}
            >
              <RefreshCw
                className={`h-4 w-4 ${accounts.isFetching || contacts.isFetching ? 'animate-spin' : ''}`}
                aria-hidden
              />
              Refresh
            </button>
            <Link to="/icp" className="ws-btn ws-btn--secondary">
              <Target className="h-4 w-4" aria-hidden />
              ICP library
            </Link>
            <Link to="/enrichment" className="ws-btn ws-btn--secondary">
              <Search className="h-4 w-4" aria-hidden />
              Enrichment
            </Link>
            <Link to="/pipeline" className="ws-btn ws-btn--primary">
              <Sparkles className="h-4 w-4" aria-hidden />
              Pipeline chat
            </Link>
          </>
        }
      />

      <div className="sdr-discovery__workspace">
        <DiscoveryRunPanel
          icpOptions={runIcpOptions}
          runIcpId={runIcpId}
          runLimit={runLimit}
          onRunIcpChange={setRunIcpId}
          onRunLimitChange={setRunLimit}
          onRun={() => startRun.mutate()}
          runPending={startRun.isPending}
          onQuickRun={handleQuickRun}
          quickRunPending={runDiscovery.isPending}
          jobId={jobId}
          jobStatus={jobQuery.data?.status}
          jobProgress={jobQuery.data?.progress}
          accountProviders={Boolean(discoveryStatus.data?.account_providers)}
          contactProvider={String(discoveryStatus.data?.contact_provider ?? 'Not configured')}
        />

        <DiscoveryAccountsPanel
          accounts={accounts.data ?? []}
          contacts={contacts.data ?? []}
          icpFilter={icpFilter}
          icpOptions={icpOptions}
          onIcpFilterChange={setIcpFilter}
          isLoading={accounts.isLoading}
          isFetching={accounts.isFetching || contacts.isFetching}
          error={accounts.error}
          onRetry={refreshResults}
          onQuickRun={handleQuickRun}
          quickRunPending={runDiscovery.isPending}
        />
      </div>
    </section>
  )
}
