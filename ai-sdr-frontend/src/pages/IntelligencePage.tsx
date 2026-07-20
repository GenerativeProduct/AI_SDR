import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FlaskConical, RefreshCw, Search } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import {
  useDiscoveredAccounts,
  useDiscoveredContacts,
  useEnrichmentList,
  useIntelligenceList,
  useIntelligenceRankingStatus,
} from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import { IntelligenceAnalyzePanel } from '../components/intelligence/IntelligenceAnalyzePanel'
import { IntelligenceResultsPanel } from '../components/intelligence/IntelligenceResultsPanel'
import { PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function IntelligencePage() {
  const qc = useQueryClient()
  const [contactId, setContactId] = useState('')

  const list = useIntelligenceList()
  const rankingStatus = useIntelligenceRankingStatus()
  const accounts = useDiscoveredAccounts()
  const contacts = useDiscoveredContacts()
  const enrichments = useEnrichmentList()

  const contactOptions = useMemo(
    () =>
      (contacts.data ?? []).map((contact) => ({
        value: contact.contact_id,
        label: `${contact.full_name} (${contact.title})`,
      })),
    [contacts.data],
  )

  const selectedContact = (contacts.data ?? []).find((contact) => contact.contact_id === contactId)
  const selectedAccount = (accounts.data ?? []).find((account) => account.account_id === selectedContact?.account_id)
  const hasEnrichment = Boolean(
    enrichments.data?.some((item) => item.account_id === selectedContact?.account_id),
  )

  const analyze = useMutation({
    mutationFn: async () => {
      const contact = (contacts.data ?? []).find((item) => item.contact_id === contactId)
      const account = (accounts.data ?? []).find((item) => item.account_id === contact?.account_id)
      const enrichment = (enrichments.data ?? []).find((item) => item.account_id === contact?.account_id)
      return api.post('/prospect-intelligence/analyze', {
        account,
        contact,
        enrichment,
        icp_context: {},
      })
    },
    onSuccess: () => {
      toast.success('Analysis complete')
      qc.invalidateQueries({ queryKey: queryKeys.intelligence.all })
    },
    onError: () => toast.error('Analysis failed'),
  })

  const rows = Array.isArray(list.data) ? list.data : []

  const refreshAll = () => {
    list.refetch()
    contacts.refetch()
    accounts.refetch()
    enrichments.refetch()
  }

  const rankingReady = Boolean(rankingStatus.data?.models_ready ?? rankingStatus.data?.ranking_ready)

  return (
    <section className="sdr-intelligence">
      <PageHeader
        embedded
        flush
        className="sdr-intelligence__header !mb-0"
        eyebrow="Pipeline"
        title={pageTitles['/intelligence'] ?? 'Intelligence'}
        description="Propensity, intent, and priority scoring — turn enrichment into ranked outbound targets."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={list.isFetching}
              onClick={refreshAll}
            >
              <RefreshCw className={`h-4 w-4 ${list.isFetching ? 'animate-spin' : ''}`} aria-hidden />
              Refresh
            </button>
            <Link to="/enrichment" className="ws-btn ws-btn--secondary">
              <Search className="h-4 w-4" aria-hidden />
              Enrichment
            </Link>
            <Link to="/qualification" className="ws-btn ws-btn--primary">
              <FlaskConical className="h-4 w-4" aria-hidden />
              Qualification
            </Link>
          </>
        }
      />

      <div className="sdr-intelligence__workspace">
        <IntelligenceAnalyzePanel
          contactId={contactId}
          contactOptions={contactOptions}
          selectedContact={selectedContact}
          companyName={selectedAccount?.company_name}
          onContactChange={setContactId}
          onAnalyze={() => analyze.mutate()}
          analyzePending={analyze.isPending}
          rankingReady={rankingReady}
          rankingDetail={String(rankingStatus.data?.detail ?? rankingStatus.data?.provider ?? 'Not configured')}
          enrichmentAvailable={hasEnrichment}
        />

        <IntelligenceResultsPanel
          rows={rows}
          isLoading={list.isLoading}
          isFetching={list.isFetching}
          error={list.error}
          onRetry={() => list.refetch()}
          onAnalyze={() => analyze.mutate()}
          analyzePending={analyze.isPending}
        />
      </div>
    </section>
  )
}
