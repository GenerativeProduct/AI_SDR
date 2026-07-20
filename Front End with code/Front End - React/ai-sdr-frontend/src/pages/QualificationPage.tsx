import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Brain, Mail, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import {
  useDiscoveredContacts,
  useEnrichmentList,
  useIntelligenceList,
  useQualificationList,
} from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import { QualificationEvaluatePanel } from '../components/qualification/QualificationEvaluatePanel'
import { QualificationResultsPanel } from '../components/qualification/QualificationResultsPanel'
import { PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function QualificationPage() {
  const qc = useQueryClient()
  const [contactId, setContactId] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const list = useQualificationList()
  const contacts = useDiscoveredContacts()
  const intelligence = useIntelligenceList()
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
  const hasIntelligence = Boolean((intelligence.data ?? []).some((item) => item.contact_id === contactId))
  const hasEnrichment = Boolean(
    enrichments.data?.some((item) => item.account_id === selectedContact?.account_id),
  )

  const evaluate = useMutation({
    mutationFn: async () => {
      const contact = (contacts.data ?? []).find((item) => item.contact_id === contactId)
      const intel = (intelligence.data ?? []).find((item) => item.contact_id === contactId)
      const enrichment = enrichments.data?.find((item) => item.account_id === contact?.account_id)
      return api.post('/qualification/evaluate', {
        contact,
        enrichment,
        intelligence: intel,
      })
    },
    onSuccess: () => {
      toast.success('Qualification complete')
      qc.invalidateQueries({ queryKey: queryKeys.qualification.all })
    },
    onError: () => toast.error('Evaluation failed'),
  })

  const results = Array.isArray(list.data) ? list.data : []

  const refreshAll = () => {
    list.refetch()
    contacts.refetch()
    intelligence.refetch()
    enrichments.refetch()
  }

  return (
    <section className="sdr-qualification">
      <PageHeader
        embedded
        flush
        className="sdr-qualification__header"
        eyebrow="Pipeline"
        title={pageTitles['/qualification'] ?? 'Qualification'}
        description="BANT and MEDDIC framework scoring with enrichment and intelligence context — route SQLs into outreach."
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
            <Link to="/intelligence" className="ws-btn ws-btn--secondary">
              <Brain className="h-4 w-4" aria-hidden />
              Intelligence
            </Link>
            <Link to="/outreach" className="ws-btn ws-btn--primary">
              <Mail className="h-4 w-4" aria-hidden />
              Outreach inbox
            </Link>
          </>
        }
      />

      <div className="sdr-qualification__workspace">
        <QualificationEvaluatePanel
          contactId={contactId}
          contactOptions={contactOptions}
          selectedContact={selectedContact}
          hasIntelligence={hasIntelligence}
          hasEnrichment={hasEnrichment}
          onContactChange={setContactId}
          onEvaluate={() => evaluate.mutate()}
          evaluatePending={evaluate.isPending}
        />

        <QualificationResultsPanel
          results={results}
          isLoading={list.isLoading}
          isFetching={list.isFetching}
          error={list.error}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          onRetry={() => list.refetch()}
          onEvaluate={() => evaluate.mutate()}
          evaluatePending={evaluate.isPending}
        />
      </div>
    </section>
  )
}
