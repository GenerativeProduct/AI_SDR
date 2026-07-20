import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Calendar, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { useCrmStatus, useCrmSyncs } from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import type { CRMSyncRecord } from '../api/types'
import { CrmStatusPanel } from '../components/crm/CrmStatusPanel'
import { CrmSyncPanel } from '../components/crm/CrmSyncPanel'
import { PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function CrmPage() {
  const qc = useQueryClient()
  const syncs = useCrmSyncs()
  const status = useCrmStatus()

  const retryCrm = useMutation({
    mutationFn: (meetingId: string) => api.post(`/meetings/${meetingId}/retry-crm`),
    onSuccess: () => {
      toast.success('Retry queued')
      qc.invalidateQueries({ queryKey: queryKeys.crm.syncs })
    },
    onError: () => toast.error('Retry failed'),
  })

  const records: CRMSyncRecord[] = Array.isArray(syncs.data) ? syncs.data : []

  const refreshAll = () => {
    syncs.refetch()
    status.refetch()
  }

  return (
    <section className="sdr-split sdr-crm">
      <PageHeader
        embedded
        flush
        className="sdr-split__header"
        eyebrow="Operations"
        title={pageTitles['/crm'] ?? 'CRM'}
        description="Sync audit log and provider status — retry failed meeting syncs."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              disabled={syncs.isFetching}
              onClick={refreshAll}
            >
              <RefreshCw className={`h-4 w-4 ${syncs.isFetching ? 'animate-spin' : ''}`} aria-hidden />
              Refresh
            </button>
            <Link to="/meetings" className="ws-btn ws-btn--primary">
              <Calendar className="h-4 w-4" aria-hidden />
              Meetings
            </Link>
          </>
        }
      />

      <div className="sdr-split__workspace">
        <CrmStatusPanel
          status={status.data as Record<string, unknown> | undefined}
          isLoading={status.isLoading}
          onRetry={() => status.refetch()}
        />
        <CrmSyncPanel
          records={records}
          isLoading={syncs.isLoading}
          isFetching={syncs.isFetching}
          error={syncs.error}
          onRetry={refreshAll}
          onRetrySync={(id) => retryCrm.mutate(id)}
          retryPending={retryCrm.isPending}
        />
      </div>
    </section>
  )
}
