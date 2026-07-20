import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Compass, RotateCcw, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { useIcpDetail, useIcpList, useIcpVersions } from '../api/hooks'
import { queryKeys } from '../api/queryKeys'
import type { ICPSuggestionResponse, ICPValidationResult } from '../api/types'
import { IcpEditorPanel } from '../components/icp/IcpEditorPanel'
import { IcpLibraryPanel } from '../components/icp/IcpLibraryPanel'
import { IcpVersionPanel } from '../components/icp/IcpVersionPanel'
import type { IcpWeightKey } from '../components/icp/icpConstants'
import { EMPTY_ICP_FORM, formFromIcpDetail, toIcpPayload, type IcpFormState } from '../components/icp/icpUtils'
import { InlineBanner, PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'

export function IcpPage() {
  const qc = useQueryClient()
  const [form, setForm] = useState<IcpFormState>(EMPTY_ICP_FORM)
  const [selectedIcpId, setSelectedIcpId] = useState<string | null>(null)
  const [selectedVersion, setSelectedVersion] = useState<number | undefined>()
  const [useLlm, setUseLlm] = useState(true)
  const [validation, setValidation] = useState<ICPValidationResult | null>(null)

  const icpList = useIcpList()
  const icpDetail = useIcpDetail(selectedIcpId, selectedVersion)
  const versions = useIcpVersions(selectedIcpId)

  useEffect(() => {
    if (!icpDetail.data) return
    setForm(formFromIcpDetail(icpDetail.data))
    setValidation(null)
  }, [icpDetail.data])

  const patchForm = (patch: Partial<IcpFormState>) => {
    setForm((current) => ({ ...current, ...patch }))
    setValidation(null)
  }

  const onWeightChange = (key: IcpWeightKey, value: number) => {
    setForm((current) => ({
      ...current,
      weights: { ...current.weights, [key]: value },
    }))
    setValidation(null)
  }

  const validate = useMutation({
    mutationFn: () => api.post<ICPValidationResult>('/icp/validate', toIcpPayload(form)),
    onSuccess: (data) => {
      setValidation(data)
      toast.success('ICP validated')
    },
    onError: () => toast.error('Validation failed'),
  })

  const suggest = useMutation({
    mutationFn: () =>
      api.post<ICPSuggestionResponse>('/icp/suggest', {
        ...toIcpPayload(form),
        llm_provider: useLlm ? 'ollama_local' : 'none',
      }),
    onSuccess: (data) => {
      patchForm({
        personasText: data.personas.join(', '),
        painPointsText: data.pain_points.join(', '),
      })
      toast.success('Suggestions applied')
    },
    onError: () => toast.error('Suggest failed'),
  })

  const save = useMutation({
    mutationFn: () => api.post('/icp', toIcpPayload(form)),
    onSuccess: () => {
      toast.success('ICP saved')
      qc.invalidateQueries({ queryKey: queryKeys.icp.all })
    },
    onError: () => toast.error('Save failed'),
  })

  const update = useMutation({
    mutationFn: () => api.put(`/icp/${selectedIcpId}`, toIcpPayload(form)),
    onSuccess: () => {
      toast.success('ICP updated')
      qc.invalidateQueries({ queryKey: queryKeys.icp.all })
    },
    onError: () => toast.error('Update failed'),
  })

  const versionItems = (Array.isArray(versions.data) ? versions.data : []).map((entry) => ({
    version: entry.version,
    status: entry.status,
    label: `v${entry.version} — ${entry.status}`,
  }))

  const selectedIcpName = icpList.data?.items?.find((item) => item.icp_id === selectedIcpId)?.icp_name

  const resetEditor = () => {
    setSelectedIcpId(null)
    setSelectedVersion(undefined)
    setForm({ ...EMPTY_ICP_FORM })
    setValidation(null)
  }

  return (
    <section className="sdr-icp">
      <PageHeader
        embedded
        flush
        className="sdr-icp__header"
        eyebrow="Pipeline"
        title={pageTitles['/icp'] ?? 'ICP Advanced'}
        description="Structured ideal customer profiles with scoring weights, version history, and LLM-assisted suggestions."
        actions={
          <>
            <button type="button" className="ws-btn ws-btn--secondary" onClick={resetEditor}>
              <RotateCcw className="h-4 w-4" aria-hidden />
              New draft
            </button>
            <Link to="/discovery" className="ws-btn ws-btn--secondary">
              <Compass className="h-4 w-4" aria-hidden />
              Discovery
            </Link>
            <Link to="/pipeline" className="ws-btn ws-btn--primary">
              <Sparkles className="h-4 w-4" aria-hidden />
              Pipeline chat
            </Link>
          </>
        }
      />

      {icpList.error ? (
        <div className="sdr-icp__banner">
          <InlineBanner message="Failed to load ICP library" onRetry={() => icpList.refetch()} />
        </div>
      ) : null}

      <div className="sdr-icp__workspace">
        <IcpLibraryPanel
          items={icpList.data?.items ?? []}
          total={icpList.data?.total ?? 0}
          selectedId={selectedIcpId}
          isLoading={icpList.isLoading}
          onSelect={(id) => {
            setSelectedIcpId(id)
            setSelectedVersion(undefined)
          }}
          onCreateNew={resetEditor}
        />

        <IcpEditorPanel
          form={form}
          onChange={patchForm}
          onWeightChange={onWeightChange}
          useLlm={useLlm}
          onUseLlmChange={setUseLlm}
          selectedIcpId={selectedIcpId}
          isLoadingDetail={icpDetail.isLoading && Boolean(selectedIcpId)}
          validation={validation}
          onValidate={() => validate.mutate()}
          onSuggest={() => suggest.mutate()}
          onSave={() => save.mutate()}
          onUpdate={() => update.mutate()}
          validatePending={validate.isPending}
          suggestPending={suggest.isPending}
          savePending={save.isPending}
          updatePending={update.isPending}
        />

        {selectedIcpId ? (
          <IcpVersionPanel
            versions={versionItems}
            selectedVersion={selectedVersion}
            onSelectVersion={setSelectedVersion}
            isLoading={versions.isLoading}
            selectedIcpName={selectedIcpName}
          />
        ) : null}
      </div>
    </section>
  )
}
