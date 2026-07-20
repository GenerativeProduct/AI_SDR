import { Loader2, Radio, Zap } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { toast } from 'sonner'
import { api } from '../../api/client'
import { queryKeys } from '../../api/queryKeys'
import type { ConversationThread } from '../../api/types'
import { WorkspaceField } from '../workspace'

type ConversationToolsPanelProps = {
  agentStatus?: string
}

export function ConversationToolsPanel({ agentStatus }: ConversationToolsPanelProps) {
  const qc = useQueryClient()
  const [campaignId, setCampaignId] = useState('')
  const [body, setBody] = useState('Thanks — can we schedule a demo next week?')

  const simulate = useMutation({
    mutationFn: () =>
      api.post<ConversationThread>('/conversations/inbound', {
        campaign_id: campaignId,
        body,
        channel: 'email',
        provider: 'dev-simulator',
      }),
    onSuccess: () => {
      toast.success('Inbound reply simulated')
      qc.invalidateQueries({ queryKey: queryKeys.conversations.list() })
    },
    onError: () => toast.error('Simulation failed'),
  })

  return (
    <aside className="sdr-split__left">
      <header className="sdr-split__left-header">
        <div>
          <p className="ws-heading-section">Tools</p>
          <h2 className="sdr-split__pane-title">Reply handling</h2>
          <p className="sdr-split__pane-desc">Monitor the conversation agent and simulate inbound replies in dev.</p>
        </div>
        <span className={`sdr-split__status-chip ${agentStatus ? 'sdr-split__status-chip--on' : ''}`}>
          <Radio className="h-3 w-3" aria-hidden />
          {agentStatus ?? 'Unknown'}
        </span>
      </header>

      <div className="sdr-split__left-body">
        <div className="sdr-split__meta-card">
          <p className="sdr-split__meta-card__label">Agent status</p>
          <dl className="sdr-split__meta-dl">
            <div>
              <dt>State</dt>
              <dd>{agentStatus ?? 'Not loaded'}</dd>
            </div>
            <div>
              <dt>Mode</dt>
              <dd>Human-in-the-loop approval</dd>
            </div>
          </dl>
        </div>

        {import.meta.env.DEV ? (
          <div className="sdr-split__dev-banner">
            <p className="sdr-split__dev-banner__label">Dev simulator</p>
            <div className="sdr-split__form mt-3">
              <WorkspaceField
                id="sim-campaign"
                label="Campaign ID"
                value={campaignId}
                onChange={setCampaignId}
              />
              <WorkspaceField
                id="sim-body"
                label="Inbound reply"
                type="textarea"
                rows={3}
                value={body}
                onChange={setBody}
              />
              <button
                type="button"
                className="ws-btn ws-btn--secondary w-full"
                disabled={!campaignId.trim() || simulate.isPending}
                onClick={() => simulate.mutate()}
              >
                {simulate.isPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Zap className="h-4 w-4" aria-hidden />}
                Simulate inbound
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </aside>
  )
}
