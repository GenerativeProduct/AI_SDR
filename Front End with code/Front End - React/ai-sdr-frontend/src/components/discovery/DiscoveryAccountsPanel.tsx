import { Building2, RefreshCw, Search, Target, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { DiscoveredAccount, DiscoveredContact } from '../../api/types'
import { EmptyState, InlineBanner, ListLoading, WorkspaceSelect } from '../workspace'
import { DiscoveryAccountRow } from './DiscoveryAccountRow'
import {
  accountsWithContacts,
  averageFitScore,
  formatCount,
} from './discoveryUtils'

type SelectOption = { value: string; label: string }

type DiscoveryAccountsPanelProps = {
  accounts: DiscoveredAccount[]
  contacts: DiscoveredContact[]
  icpFilter: string
  icpOptions: SelectOption[]
  onIcpFilterChange: (value: string) => void
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  onRetry: () => void
  onQuickRun: () => void
  quickRunPending: boolean
}

export function DiscoveryAccountsPanel({
  accounts,
  contacts,
  icpFilter,
  icpOptions,
  onIcpFilterChange,
  isLoading,
  isFetching,
  error,
  onRetry,
  onQuickRun,
  quickRunPending,
}: DiscoveryAccountsPanelProps) {
  const [query, setQuery] = useState('')

  const contactMap = useMemo(() => {
    const map = new Map<string, DiscoveredContact[]>()
    for (const contact of contacts) {
      const list = map.get(contact.account_id) ?? []
      list.push(contact)
      map.set(contact.account_id, list)
    }
    return map
  }, [contacts])

  const filteredAccounts = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return accounts
    return accounts.filter((account) => {
      const haystack = [
        account.company_name,
        account.industry,
        account.location,
        account.status,
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [accounts, query])

  const kpis = [
    {
      label: 'Accounts',
      value: formatCount(accounts.length),
      hint: 'Discovered companies',
      icon: Building2,
    },
    {
      label: 'Contacts',
      value: formatCount(contacts.length),
      hint: 'People linked to accounts',
      icon: Users,
    },
    {
      label: 'Avg fit',
      value: `${averageFitScore(accounts)}`,
      hint: 'Mean ICP fit score',
      icon: Target,
    },
    {
      label: 'With contacts',
      value: formatCount(accountsWithContacts(accounts, contactMap)),
      hint: 'Accounts that have people',
      icon: Users,
    },
  ]

  return (
    <section className="sdr-discovery__results">
      <header className="sdr-discovery__results-header">
        <div>
          <p className="ws-heading-section">Results</p>
          <h2 className="sdr-discovery__pane-title">Discovered accounts</h2>
          <p className="sdr-discovery__pane-desc">
            Review fit scores, contacts, and queue enrichment for promising targets.
          </p>
        </div>
        <button
          type="button"
          className="ws-btn ws-btn--secondary ws-btn--compact"
          disabled={isFetching}
          onClick={onRetry}
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} aria-hidden />
          Refresh
        </button>
      </header>

      <div className="sdr-discovery__kpi-row">
        {kpis.map((kpi) => (
          <article key={kpi.label} className="sdr-discovery-kpi">
            <span className="sdr-discovery-kpi__icon" aria-hidden>
              <kpi.icon className="h-4 w-4" />
            </span>
            <p className="ws-kpi-label">{kpi.label}</p>
            <p className="ws-kpi-value">{kpi.value}</p>
            <p className="ws-kpi-hint">{kpi.hint}</p>
          </article>
        ))}
      </div>

      <div className="sdr-discovery__filters">
        <div className="sdr-discovery__search">
          <Search className="sdr-discovery__search-icon h-4 w-4" aria-hidden />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search accounts…"
            className="sdr-discovery__search-input"
            aria-label="Search discovered accounts"
          />
        </div>
        <WorkspaceSelect
          id="discovery-filter-icp"
          label="Filter by ICP"
          value={icpFilter}
          options={icpOptions}
          onChange={onIcpFilterChange}
        />
      </div>

      <div className="sdr-discovery__results-body">
        {error ? <InlineBanner message="Failed to load accounts" onRetry={onRetry} /> : null}

        {isLoading ? (
          <ListLoading rows={5} />
        ) : filteredAccounts.length === 0 ? (
          <EmptyState
            icon={<Building2 className="h-7 w-7" aria-hidden />}
            title={query ? 'No matching accounts' : 'No discovered accounts'}
            description={
              query
                ? 'Try a different search term or clear the ICP filter.'
                : 'Run discovery with a saved ICP or try a quick sample run.'
            }
            action={
              !query ? (
                <button type="button" className="ws-btn ws-btn--primary" disabled={quickRunPending} onClick={onQuickRun}>
                  Quick sample run
                </button>
              ) : null
            }
          />
        ) : (
          <div className="sdr-discovery-account-list">
            {filteredAccounts.map((account) => (
              <DiscoveryAccountRow
                key={account.account_id}
                account={account}
                contacts={contactMap.get(account.account_id) ?? []}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
