import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Building2, ChevronDown, Loader2, Mail, Search, UserRound } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { api } from '../../api/client'
import { queryKeys } from '../../api/queryKeys'
import type { DiscoveredAccount, DiscoveredContact } from '../../api/types'
import { cn } from '../../lib/utils'
import { StatusBadge } from '../workspace'
import { fitTone } from './discoveryUtils'

type DiscoveryAccountRowProps = {
  account: DiscoveredAccount
  contacts: DiscoveredContact[]
}

export function DiscoveryAccountRow({ account, contacts }: DiscoveryAccountRowProps) {
  const [expanded, setExpanded] = useState(false)
  const qc = useQueryClient()
  const tone = fitTone(account.fit_score)

  const research = useMutation({
    mutationFn: () =>
      api.post('/enrichment/research', {
        account,
        contacts,
        llm_provider: 'ollama_local',
      }),
    onSuccess: () => {
      toast.success('Enrichment research queued')
      qc.invalidateQueries({ queryKey: queryKeys.enrichment.all })
    },
    onError: () => toast.error('Enrichment research failed'),
  })

  return (
    <article className="sdr-discovery-account">
      <div className="sdr-discovery-account__main">
        <span className="sdr-discovery-account__icon" aria-hidden>
          <Building2 className="h-4 w-4" />
        </span>

        <div className="sdr-discovery-account__copy min-w-0 flex-1">
          <div className="sdr-discovery-account__head">
            <h3 className="sdr-discovery-account__name">{account.company_name}</h3>
            <StatusBadge status={account.status} />
          </div>
          <p className="sdr-discovery-account__meta">
            {account.industry} · {account.location} · {account.employee_count.toLocaleString()} employees
          </p>
          <div className="sdr-discovery-account__fit">
            <div className="sdr-discovery-account__fit-meta">
              <span>ICP fit</span>
              <span className={cn('sdr-discovery-account__fit-value', `sdr-discovery-account__fit-value--${tone}`)}>
                {account.fit_score}/100
              </span>
            </div>
            <div className="ws-funnel-track sdr-discovery-account__fit-track" aria-hidden>
              <div
                className={cn('ws-funnel-fill sdr-discovery-account__fit-fill', `sdr-discovery-account__fit-fill--${tone}`)}
                style={{ width: `${Math.max(account.fit_score, 4)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="sdr-discovery-account__aside">
          <span className="sdr-discovery-account__contacts-pill">
            <UserRound className="h-3.5 w-3.5" aria-hidden />
            {contacts.length} contact{contacts.length === 1 ? '' : 's'}
          </span>
          <div className="sdr-discovery-account__actions">
            <button
              type="button"
              className="ws-btn ws-btn--secondary ws-btn--compact"
              disabled={research.isPending}
              onClick={() => research.mutate()}
            >
              {research.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Search className="h-3.5 w-3.5" aria-hidden />}
              Enrich
            </button>
            <button
              type="button"
              className="ws-btn ws-btn--ghost ws-btn--compact"
              aria-expanded={expanded}
              onClick={() => setExpanded((open) => !open)}
            >
              {expanded ? 'Hide' : 'Contacts'}
              <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', expanded && 'rotate-180')} aria-hidden />
            </button>
          </div>
        </div>
      </div>

      {expanded ? (
        <div className="sdr-discovery-account__contacts">
          {contacts.length === 0 ? (
            <p className="sdr-discovery-account__contacts-empty">No contacts discovered for this account yet.</p>
          ) : (
            <ul className="sdr-discovery-contact-list">
              {contacts.map((contact) => (
                <li key={contact.contact_id} className="sdr-discovery-contact">
                  <span className="sdr-discovery-contact__avatar" aria-hidden>
                    <UserRound className="h-3.5 w-3.5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="sdr-discovery-contact__name">{contact.full_name}</p>
                    <p className="sdr-discovery-contact__title">{contact.title}</p>
                  </div>
                  <div className="sdr-discovery-contact__meta">
                    <span className="sdr-discovery-contact__score">{contact.persona_match_score}% match</span>
                    <span className="sdr-discovery-contact__email">
                      <Mail className="h-3 w-3" aria-hidden />
                      {contact.email ?? 'No email'}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </article>
  )
}
