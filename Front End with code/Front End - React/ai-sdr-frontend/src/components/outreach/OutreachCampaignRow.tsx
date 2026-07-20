import { Mail } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { OutreachCampaign } from '../../api/types'
import { CampaignChannelBadge, StatusBadge } from '../workspace'
import { campaignKey } from './outreachUtils'

type OutreachCampaignRowProps = {
  campaign: OutreachCampaign
  selected: boolean
  onSelect: () => void
}

export function OutreachCampaignRow({ campaign, selected, onSelect }: OutreachCampaignRowProps) {
  return (
    <button
      type="button"
      className={cn('sdr-outreach-result ws-focus-ring', selected && 'sdr-outreach-result--active')}
      onClick={onSelect}
    >
      <span className="sdr-outreach-result__icon" aria-hidden>
        <Mail className="h-4 w-4" />
      </span>
      <span className="sdr-outreach-result__copy min-w-0">
        <span className="sdr-outreach-result__head">
          <span className="sdr-outreach-result__name">
            {campaign.contact_name ?? campaign.campaign_id}
          </span>
          <StatusBadge status={String(campaign.status)} />
        </span>
        {campaign.subject ? (
          <span className="sdr-outreach-result__subject">{campaign.subject}</span>
        ) : null}
        <span className="sdr-outreach-result__meta">
          {campaign.channel ? <CampaignChannelBadge channel={String(campaign.channel)} /> : null}
        </span>
      </span>
    </button>
  )
}

export { campaignKey }
