import { useMutation } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { RotateCcw } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { useJobPoll } from '../api/hooks'
import type {
  ICPSuggestionResponse,
  ICPValidationResult,
  JobCreateResponse,
  SDRPipelineResponse,
} from '../api/types'
import { PipelineComposerPanel } from '../components/pipeline/PipelineComposerPanel'
import { PipelineRunPanel } from '../components/pipeline/PipelineRunPanel'
import { PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'
import { usePipelineStore } from '../stores/authStore'

function buildIcpPayload(prompt: string, suggestion?: ICPSuggestionResponse) {
  return {
    industries: suggestion?.personas?.length ? ['SaaS'] : [],
    geographies: ['US'],
    target_personas: suggestion?.personas ?? [],
    pain_points: suggestion?.pain_points ?? [],
    offer_summary: prompt,
    created_by: 'frontend',
  }
}

export function PipelinePage() {
  const [prompt, setPrompt] = useState('')
  const [suggestion, setSuggestion] = useState<ICPSuggestionResponse | null>(null)
  const [validation, setValidation] = useState<ICPValidationResult | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [syncMode, setSyncMode] = useState(false)
  const lastResult = usePipelineStore((s) => s.lastResult)
  const setLastResult = usePipelineStore((s) => s.setLastResult)

  const jobQuery = useJobPoll(jobId)

  useEffect(() => {
    if (jobQuery.data?.status === 'completed' && jobQuery.data.result) {
      setLastResult(jobQuery.data.result as unknown as Record<string, unknown>)
    }
  }, [jobQuery.data, setLastResult])

  const suggest = useMutation({
    mutationFn: () =>
      api.post<ICPSuggestionResponse>('/icp/suggest', {
        prompt,
        industries: ['SaaS'],
        target_personas: ['RevOps'],
      }),
    onSuccess: (data) => {
      setSuggestion(data)
      toast.success('ICP suggestions ready')
    },
    onError: () => toast.error('Suggest failed'),
  })

  const validate = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.post<ICPValidationResult>('/icp/validate', payload),
    onSuccess: (data) => {
      setValidation(data)
      toast.success('ICP validated')
    },
    onError: () => toast.error('Validation failed'),
  })

  const runPipeline = useMutation({
    mutationFn: async () => {
      const icpPayload = buildIcpPayload(prompt, suggestion ?? undefined)
      await validate.mutateAsync(icpPayload)
      const syncQs = syncMode ? '?sync=true' : ''
      const job = await api.post<JobCreateResponse | SDRPipelineResponse>(
        `/sdr/pipeline/run${syncQs}`,
        {
          icp_payload: icpPayload,
          discovery_limit: 3,
          enrich_top_accounts: 1,
        },
      )
      if ('job_id' in job) {
        setJobId(job.job_id)
        setLastResult(null)
      } else {
        setLastResult(job as unknown as Record<string, unknown>)
      }
      return job
    },
    onSuccess: () => toast.success(syncMode ? 'Pipeline completed' : 'Pipeline started'),
    onError: () => toast.error('Pipeline failed to start'),
  })

  const result = (lastResult ?? jobQuery.data?.result) as SDRPipelineResponse | undefined
  const isRunning = Boolean(jobId && jobQuery.data && !['completed', 'failed'].includes(jobQuery.data.status))

  const resetSession = () => {
    setPrompt('')
    setSuggestion(null)
    setValidation(null)
    setJobId(null)
    setLastResult(null)
  }

  return (
    <section className="sdr-pipeline">
      <PageHeader
        embedded
        flush
        className="sdr-pipeline__header"
        eyebrow="Overview"
        title={pageTitles['/pipeline'] ?? 'Pipeline Chat'}
        description="Natural-language ICP composer with a live seven-stage agent run — discovery through follow-up in one workflow."
        actions={
          <>
            <button
              type="button"
              className="ws-btn ws-btn--secondary"
              onClick={resetSession}
              disabled={isRunning || runPipeline.isPending}
            >
              <RotateCcw className="h-4 w-4" aria-hidden />
              Reset
            </button>
            <Link to="/discovery" className="ws-btn ws-btn--secondary">
              Discovery module
            </Link>
            <Link to="/outreach" className="ws-btn ws-btn--primary">
              Outreach inbox
            </Link>
          </>
        }
      />

      <div className="sdr-pipeline__workspace">
        <PipelineComposerPanel
          prompt={prompt}
          onPromptChange={setPrompt}
          syncMode={syncMode}
          onSyncModeChange={setSyncMode}
          suggestion={suggestion}
          validation={validation}
          onSuggest={() => suggest.mutate()}
          onValidate={() => validate.mutate(buildIcpPayload(prompt, suggestion ?? undefined))}
          onRun={() => runPipeline.mutate()}
          suggestPending={suggest.isPending}
          validatePending={validate.isPending}
          runPending={runPipeline.isPending}
          isRunning={isRunning}
        />

        <PipelineRunPanel
          jobId={jobId}
          job={jobQuery.data}
          result={result}
          hasPrompt={Boolean(prompt.trim())}
        />
      </div>
    </section>
  )
}
