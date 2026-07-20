import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Brain, Compass, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import {
  useDiscoveredAccounts,
  useDiscoveredContacts,
  useEnrichmentList,
  useEnrichmentStatus,
} from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import type { DiscoveredAccount } from '../api/types'
import { EnrichmentResearchPanel } from '../components/enrichment/EnrichmentResearchPanel'
import { EnrichmentResultsPanel } from '../components/enrichment/EnrichmentResultsPanel'
import { PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function EnrichmentPage() {
  const qc = useQueryClient()
  const [accountId, setAccountId] = useState('')
  const [useLlm, setUseLlm] = useState(true)

  const list = useEnrichmentList()
  const status = useEnrichmentStatus()
  const accounts = useDiscoveredAccounts()
  const contacts = useDiscoveredContacts(accountId || undefined)

  const accountOptions = useMemo(
    () => (accounts.data ?? []).map((account) => ({ value: account.account_id, label: account.company_name })),
    [accounts.data],
  )

  const selectedAccount = (accounts.data ?? []).find((account) => account.account_id === accountId) as
    | DiscoveredAccount
    | undefined

  const research = useMutation({
    mutationFn: async () => {
      const account = (accounts.data ?? []).find((item) => item.account_id === accountId) as DiscoveredAccount
      return api.post('/enrichment/research', {
        account,
        contacts: contacts.data ?? [],
        llm_provider: useLlm ? 'ollama_local' : 'none',
      })
    },
    onSuccess: () => {
      toast.success('Enrichment research complete')
      qc.invalidateQueries({ queryKey: queryKeys.enrichment.all })
    },
    onError: () => toast.error('Research failed'),
  })

  const results = Array.isArray(list.data) ? list.data : []

  const refreshAll = () => {
    list.refetch()
    accounts.refetch()
    if (accountId) contacts.refetch()
  }

  return (
    <section className="sdr-enrichment">
      <PageHeader
        embedded
        flush
        className="sdr-enrichment__header"
        eyebrow="Pipeline"
        title={pageTitles['/enrichment'] ?? 'Enrichment'}
        description="Deep research on discovered accounts — company briefs, live signals, and personalization angles for downstream intelligence."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={list.isFetching || accounts.isFetching}
              onClick={refreshAll}
            >
              <RefreshCw
                className={`h-4 w-4 ${list.isFetching || accounts.isFetching ? 'animate-spin' : ''}`}
                aria-hidden
              />
              Refresh
            </button>
            <Link to="/discovery" className="ws-btn ws-btn--secondary">
              <Compass className="h-4 w-4" aria-hidden />
              Discovery
            </Link>
            <Link to="/intelligence" className="ws-btn ws-btn--primary">
              <Brain className="h-4 w-4" aria-hidden />
              Intelligence
            </Link>
          </>
        }
      />

      <div className="sdr-enrichment__workspace">
        <EnrichmentResearchPanel
          accountId={accountId}
          accountOptions={accountOptions}
          selectedAccount={selectedAccount}
          contactCount={contacts.data?.length ?? 0}
          useLlm={useLlm}
          onAccountChange={setAccountId}
          onUseLlmChange={setUseLlm}
          onResearch={() => research.mutate()}
          researchPending={research.isPending}
          liveSearchConfigured={Boolean(status.data?.live_search_configured)}
          statusDetail={String(status.data?.detail ?? status.data?.live_search_configured ?? 'Not configured')}
        />

        <EnrichmentResultsPanel
          results={results}
          isLoading={list.isLoading}
          isFetching={list.isFetching}
          error={list.error}
          onRetry={() => list.refetch()}
          onRunResearch={() => research.mutate()}
          researchPending={research.isPending}
        />
      </div>
    </section>
  )
}
